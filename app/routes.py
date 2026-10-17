from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import current_user
from app.models import db, DietPlan
from app.services.calculator import calculate_targets, calculate_bmi
from app.services.ai_service import generate_smart_diet_plan

main_bp = Blueprint('main', __name__)

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
        weight = float(data.get("weight", 70))
        height = float(data.get("height", 170))
        age = int(data.get("age", 25))
        gender = data.get("gender", "male")
        activity = data.get("activity_level", "moderately_active")
        goal = data.get("goal", "weight_loss")
        dietary_pref = data.get("dietary_preference", "vegetarian")
        
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
        
        user_name = data.get("user_name", "").strip() or default_name
        age = int(data.get("age", 25))
        gender = data.get("gender", "male")
        weight = float(data.get("weight", 70.0))
        target_weight = float(data.get("target_weight")) if data.get("target_weight") else None
        height = float(data.get("height", 170.0))
        activity_level = data.get("activity_level", "moderately_active")
        goal = data.get("goal", "weight_loss")
        dietary_preference = data.get("dietary_preference", "vegetarian")
        allergies = data.get("allergies", "").strip()
        custom_title = data.get("title", f"{user_name}'s {goal.title().replace('_', ' ')} Plan")
        
        # Check custom API key sent from UI, fallback to server config
        custom_key = data.get("gemini_api_key", "").strip() or current_app.config.get("GEMINI_API_KEY", "")
        
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
            print(f"INFO: Database save bypassed or failed ({db_err}). Proceeding in stateless mode.")
            
        return jsonify({
            "success": True,
            "plan_id": plan_id,
            "is_ai_generated": is_ai,
            "targets": targets,
            "plan_data": plan_data,
            "redirect_url": f"/plan/{plan_id}" if plan_id else None
        })
        
    except Exception as e:
        print(f"Error in api_generate: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

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
