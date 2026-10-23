from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app, session
from flask_login import current_user
from app.models import db, DietPlan
from app.services.calculator import calculate_targets, calculate_bmi
from app.services.ai_service import generate_smart_diet_plan

main_bp = Blueprint('main', __name__)

def _safe_float(val, default=0.0):
    try:
        if val is None or str(val).strip() == "":
            return default
        return float(val)
    except (ValueError, TypeError):
        return default

def _safe_int(val, default=0):
    try:
        if val is None or str(val).strip() == "":
            return default
        return int(float(val))
    except (ValueError, TypeError):
        return default

@main_bp.route('/')
def index():
    """Landing and Diet Plan Creator Wizard."""
    return render_template('index.html')

@main_bp.route('/health')
def health():
    """Health check endpoint for Vercel and uptime monitoring."""
    db_status = "connected"
    try:
        # Quick ping
        db.session.execute(db.text("SELECT 1"))
    except Exception as e:
        db_status = f"unreachable / fallback ({str(e)})"
        
    return jsonify({
        "status": "healthy",
        "service": "Special AI Diet Planner",
        "database": db_status,
        "gemini_configured": bool(current_app.config.get("GEMINI_API_KEY"))
    }), 200

@main_bp.route('/api/calculate', methods=['POST'])
def api_calculate():
    """Real-time calculation endpoint for instant live-preview as user types."""
    try:
        data = request.get_json() or {}
        weight = _safe_float(data.get("weight"), 70.0)
        height = _safe_float(data.get("height"), 170.0)
        age = _safe_int(data.get("age"), 25)
        gender = str(data.get("gender") or "male").strip().lower()
        activity = str(data.get("activity_level") or "moderately_active").strip().lower()
        goal = str(data.get("goal") or "weight_loss").strip().lower()
        dietary_pref = str(data.get("dietary_preference") or "vegetarian").strip().lower()
        
        targets = calculate_targets(
            weight_kg=weight,
            height_cm=height,
            age=age,
            gender=gender,
            activity_level=activity,
            goal=goal,
            dietary_pref=dietary_pref
        )
        return jsonify({"success": True, "targets": targets})
    except Exception as err:
        return jsonify({"success": False, "error": str(err)}), 400

@main_bp.route('/api/generate', methods=['POST'])
def api_generate():
    """Generate and persist personalized AI Diet Plan."""
    try:
        data = request.get_json() or {}
        
        # Determine logged in user details if available
        user_id = current_user.id if current_user.is_authenticated else None
        default_name = current_user.name if current_user.is_authenticated else "Valued Client"
        
        user_name = str(data.get("user_name") or "").strip() or default_name
        age = _safe_int(data.get("age"), 25)
        gender = str(data.get("gender") or "male").strip().lower()
        weight = _safe_float(data.get("weight"), 70.0)
        target_weight_raw = data.get("target_weight")
        target_weight = _safe_float(target_weight_raw, None) if target_weight_raw not in (None, "", "null") else None
        height = _safe_float(data.get("height"), 170.0)
        activity_level = str(data.get("activity_level") or "moderately_active").strip().lower()
        goal = str(data.get("goal") or "weight_loss").strip().lower()
        dietary_preference = str(data.get("dietary_preference") or "vegetarian").strip().lower()
        allergies = str(data.get("allergies") or "").strip()
        custom_title = str(data.get("title") or f"{user_name}'s {goal.title().replace('_', ' ')} Plan").strip()
        
        # Check custom API key sent from UI, fallback to server config
        custom_key = str(data.get("gemini_api_key") or "").strip() or current_app.config.get("GEMINI_API_KEY", "")
        
        profile = {
            "user_name": user_name,
            "age": age,
            "gender": gender,
            "weight": weight,
            "target_weight": target_weight,
            "height": height,
            "activity_level": activity_level,
            "goal": goal,
            "dietary_preference": dietary_preference,
            "allergies": allergies
        }
        
        targets, plan_data, is_ai = generate_smart_diet_plan(profile, api_key=custom_key)
        
        # Store in session as guaranteed fallback so user always sees their plan
        session['latest_plan'] = {
            "title": custom_title,
            "user_name": user_name,
            "age": age,
            "gender": gender,
            "weight": weight,
            "target_weight": target_weight,
            "height": height,
            "activity_level": activity_level,
            "goal": goal,
            "dietary_preference": dietary_preference,
            "allergies": allergies,
            "bmr": targets["bmr"],
            "tdee": targets["tdee"],
            "target_calories": targets["calorie_target"],
            "protein_g": targets["protein_g"],
            "carbs_g": targets["carbs_g"],
            "fat_g": targets["fat_g"],
            "ai_generated": is_ai,
            "plan_data": plan_data
        }
        
        # Save to Database with graceful failure handling
        plan_id = None
        try:
            new_plan = DietPlan(
                user_id=user_id,
                title=custom_title,
                user_name=user_name,
                age=age,
                gender=gender,
                weight=weight,
                target_weight=target_weight,
                height=height,
                activity_level=activity_level,
                goal=goal,
                dietary_preference=dietary_preference,
                allergies=allergies,
                bmr=targets["bmr"],
                tdee=targets["tdee"],
                target_calories=targets["calorie_target"],
                protein_g=targets["protein_g"],
                carbs_g=targets["carbs_g"],
                fat_g=targets["fat_g"],
                ai_generated=is_ai
            )
            new_plan.set_plan_data(plan_data)
            
            db.session.add(new_plan)
            db.session.commit()
            plan_id = new_plan.id
        except Exception as db_err:
            db.session.rollback()
            print(f"INFO: Database save bypassed or failed ({db_err}). Proceeding with session fallback.")
            
        redirect_url = f"/plan/{plan_id}" if plan_id else "/plan/latest"
            
        return jsonify({
            "success": True,
            "plan_id": plan_id,
            "is_ai_generated": is_ai,
            "targets": targets,
            "plan_data": plan_data,
            "redirect_url": redirect_url
        })
        
    except Exception as e:
        print(f"Error in api_generate: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@main_bp.route('/plan/latest')
def view_latest_plan():
    """Render latest generated plan from session or recent database record."""
    from datetime import datetime, timezone
    plan_dict = session.get('latest_plan')
    if plan_dict:
        dummy_plan = DietPlan(
            title=plan_dict.get("title", "My Personalized Diet Plan"),
            user_name=plan_dict.get("user_name", "Valued Client"),
            age=plan_dict.get("age", 25),
            gender=plan_dict.get("gender", "male"),
            weight=plan_dict.get("weight", 70),
            target_weight=plan_dict.get("target_weight"),
            height=plan_dict.get("height", 170),
            activity_level=plan_dict.get("activity_level", "moderately_active"),
            goal=plan_dict.get("goal", "weight_loss"),
            dietary_preference=plan_dict.get("dietary_preference", "vegetarian"),
            allergies=plan_dict.get("allergies", ""),
            bmr=plan_dict.get("bmr", 1600),
            tdee=plan_dict.get("tdee", 2200),
            target_calories=plan_dict.get("target_calories", 2000),
            protein_g=plan_dict.get("protein_g", 150),
            carbs_g=plan_dict.get("carbs_g", 200),
            fat_g=plan_dict.get("fat_g", 55),
            ai_generated=plan_dict.get("ai_generated", False)
        )
        dummy_plan.created_at = datetime.now(timezone.utc)
        dummy_plan.set_plan_data(plan_dict.get("plan_data", {}))
        return render_template('plan.html', plan=dummy_plan)
        
    try:
        latest = db.session.query(DietPlan).order_by(DietPlan.id.desc()).first()
        if latest:
            return redirect(url_for('main.view_plan', plan_id=latest.id))
    except Exception:
        pass
        
    flash("No recent plan found. Please generate a new plan.", "info")
    return redirect(url_for('main.index'))

@main_bp.route('/plan/<int:plan_id>')
def view_plan(plan_id):
    """Render saved plan page."""
    try:
        plan = db.session.get(DietPlan, plan_id)
        if not plan:
            flash("Plan not found.", "warning")
            return redirect(url_for('main.index'))
        return render_template('plan.html', plan=plan)
    except Exception as e:
        flash(f"Plan not found or database unavailable: {e}", "warning")
        return redirect(url_for('main.index'))

@main_bp.route('/history')
def history():
    """List all saved diet plans with user-specific prioritization."""
    plans = []
    try:
        if current_user.is_authenticated:
            # Query plans created by current user
            user_plans = DietPlan.query.filter_by(user_id=current_user.id).order_by(DietPlan.created_at.desc()).all()
            if user_plans:
                plans = user_plans
            else:
                # If user hasn't made any plans yet, show latest community plans
                plans = DietPlan.query.order_by(DietPlan.created_at.desc()).limit(20).all()
        else:
            plans = DietPlan.query.order_by(DietPlan.created_at.desc()).limit(50).all()
    except Exception as e:
        print(f"Could not query history: {e}")
        flash("Database query encountered an issue or is not yet configured.", "info")
        
    return render_template('history.html', plans=plans)

@main_bp.route('/api/plan/<int:plan_id>', methods=['DELETE'])
def delete_plan(plan_id):
    """Delete a plan by ID."""
    try:
        plan = db.session.get(DietPlan, plan_id)
        if plan:
            db.session.delete(plan)
            db.session.commit()
            return jsonify({"success": True})
        return jsonify({"success": False, "error": "Plan not found"}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
