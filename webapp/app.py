"""Flask Web Application — тонкий клиент логистического сервиса."""

from __future__ import annotations

import os
from datetime import datetime
from functools import wraps

from flask import (
    Flask, flash, redirect, render_template,
    request, session, url_for,
)

from logistics.api.client import LogisticsClient

# ── Приложение ────────────────────────────────────────────────────────

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-logistics-2025")

API_HOST = os.environ.get("API_HOST", "127.0.0.1")
API_PORT = int(os.environ.get("API_PORT", "9090"))


def get_client() -> LogisticsClient:
    return LogisticsClient(host=API_HOST, port=API_PORT)


# ── Обёртка для вызовов API ───────────────────────────────────────────


def api_call(func, *args, **kwargs):
    """Вызвать метод API-клиента, вернуть (data, error)."""
    try:
        result = func(*args, **kwargs)
        if result.get("status") == "error":
            return None, result.get("message", "Неизвестная ошибка")
        return result.get("data"), None
    except ConnectionRefusedError:
        return None, "Сервис недоступен. Проверьте, запущен ли TCP-сервер."
    except Exception as e:
        return None, str(e)


# ── Декораторы ────────────────────────────────────────────────────────


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            flash("Пожалуйста, войдите в систему", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "user" not in session:
                flash("Пожалуйста, войдите в систему", "warning")
                return redirect(url_for("login"))
            if session["user"]["role"] not in roles:
                flash("Недостаточно прав", "danger")
                return redirect(url_for("dashboard"))
            return f(*args, **kwargs)
        return decorated
    return decorator


# ── Фильтры Jinja2 ───────────────────────────────────────────────────

STATUS_LABELS = {
    "CREATED": "Создан",
    "PROCESSING": "В обработке",
    "WAITING_DROP_OFF": "Ожидает сдачи",
    "IN_TRANSIT": "В пути",
    "ARRIVED": "Прибыл",
    "DELIVERED": "Доставлен",
    "CANCELLED": "Отменён",
}

STATUS_COLORS = {
    "CREATED": "secondary",
    "PROCESSING": "info",
    "WAITING_DROP_OFF": "warning",
    "IN_TRANSIT": "primary",
    "ARRIVED": "success",
    "DELIVERED": "dark",
    "CANCELLED": "danger",
}

TRANSPORT_LABELS = {
    "ROAD": "🚛 Авто",
    "RAIL": "🚂 Ж/д",
    "AIR": "✈️ Авиа",
    "SEA": "🚢 Море",
}


@app.template_filter("fmt_date")
def fmt_date(value):
    if not value:
        return "—"
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except (ValueError, TypeError):
            return value
    return value.strftime("%d.%m.%Y %H:%M")


@app.template_filter("fmt_money")
def fmt_money(value):
    if value is None or value == "None":
        return "—"
    try:
        return f"{float(value):,.2f} ₽".replace(",", " ")
    except (ValueError, TypeError):
        return str(value)


@app.template_filter("fmt_minutes")
def fmt_minutes(value):
    if not value:
        return "—"
    m = int(value)
    if m < 60:
        return f"{m} мин"
    h, rem = divmod(m, 60)
    if h < 24:
        return f"{h}ч {rem}мин" if rem else f"{h}ч"
    d, hrs = divmod(h, 24)
    return f"{d}д {hrs}ч"


@app.template_filter("status_label")
def status_label(value):
    return STATUS_LABELS.get(value, value)


@app.template_filter("status_color")
def status_color(value):
    return STATUS_COLORS.get(value, "secondary")


@app.template_filter("transport_label")
def transport_label(value):
    return TRANSPORT_LABELS.get(value, value)


@app.template_filter("short_uuid")
def short_uuid(value):
    if not value:
        return "—"
    s = str(value)
    return s[:8] + "…" if len(s) > 8 else s


# ── Контекст для всех шаблонов ────────────────────────────────────────

@app.context_processor
def inject_globals():
    return {
        "STATUS_LABELS": STATUS_LABELS,
        "STATUS_COLORS": STATUS_COLORS,
    }


# =====================================================================
#  МАРШРУТЫ
# =====================================================================


# ── Главная ───────────────────────────────────────────────────────────

@app.route("/")
def index():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


# ── Аутентификация ────────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_val = request.form.get("login", "").strip()
        password = request.form.get("password", "")
        if not login_val or not password:
            flash("Заполните все поля", "warning")
            return render_template("login.html")

        data, err = api_call(get_client().login, login_val, password)
        if err:
            flash(err, "danger")
            return render_template("login.html")

        session["user"] = data
        flash(f"Добро пожаловать, {data.get('full_name', data['login'])}!", "success")
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        login_val = request.form.get("login", "").strip()
        password = request.form.get("password", "")
        password2 = request.form.get("password2", "")
        full_name = request.form.get("full_name", "").strip()

        if not login_val or not password:
            flash("Заполните обязательные поля", "warning")
            return render_template("register.html")
        if password != password2:
            flash("Пароли не совпадают", "warning")
            return render_template("register.html")

        data, err = api_call(
            get_client().register, login_val, password, full_name or login_val,
        )
        if err:
            flash(err, "danger")
            return render_template("register.html")

        session["user"] = data
        flash("Регистрация успешна!", "success")
        return redirect(url_for("dashboard"))

    return render_template("register.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Вы вышли из системы", "info")
    return redirect(url_for("index"))


# ── Дашборд ──────────────────────────────────────────────────────────

@app.route("/dashboard")
@login_required
def dashboard():
    user = session["user"]
    orders = []

    if user["role"] in ("MANAGER", "ADMIN"):
        data, err = api_call(get_client().list_all_orders)
    else:
        data, err = api_call(get_client().list_orders, user["id"])

    if data:
        orders = data.get("orders", [])

    return render_template("dashboard.html", orders=orders[:10])


# ── Мои заказы ────────────────────────────────────────────────────────

@app.route("/orders")
@login_required
def my_orders():
    user = session["user"]
    data, err = api_call(get_client().list_orders, user["id"])
    if err:
        flash(err, "danger")
        orders = []
    else:
        orders = data.get("orders", [])
    return render_template("my_orders.html", orders=orders)


# ── Создание заказа ───────────────────────────────────────────────────

@app.route("/orders/create", methods=["GET", "POST"])
@login_required
def create_order():
    # Получаем локации для формы
    loc_data, loc_err = api_call(get_client().list_locations)
    locations = loc_data.get("locations", []) if loc_data else []

    if request.method == "POST":
        try:
            data, err = api_call(
                get_client().create_order,
                sender_id=session["user"]["id"],
                origin_id=int(request.form["origin_id"]),
                dest_id=int(request.form["dest_id"]),
                weight_kg=float(request.form["weight_kg"]),
                height_m=float(request.form["height_m"]),
                width_m=float(request.form["width_m"]),
                length_m=float(request.form["length_m"]),
                description=request.form.get("description", ""),
                is_fragile="is_fragile" in request.form,
                is_dangerous="is_dangerous" in request.form,
                is_liquid="is_liquid" in request.form,
                is_perishable="is_perishable" in request.form,
                is_crushable="is_crushable" in request.form,
                req_temp_control="req_temp_control" in request.form,
                strategy=request.form.get("strategy", "cheapest"),
            )
            if err:
                flash(err, "danger")
                return render_template("create_order.html", locations=locations)

            order_id = data.get("id", "")
            flash("Заказ успешно создан!", "success")
            return redirect(url_for("order_detail", order_id=order_id))

        except (ValueError, KeyError) as e:
            flash(f"Ошибка в данных формы: {e}", "danger")

    return render_template("create_order.html", locations=locations)


# ── Детали заказа ─────────────────────────────────────────────────────

@app.route("/orders/<order_id>")
@login_required
def order_detail(order_id: str):
    data, err = api_call(get_client().get_order, order_id)
    if err:
        flash(err, "danger")
        return redirect(url_for("my_orders"))

    tracking_data, _ = api_call(get_client().get_tracking, order_id)
    events = tracking_data.get("events", []) if tracking_data else []

    return render_template("order_detail.html", order=data, events=events)


# ── Калькулятор маршрута ──────────────────────────────────────────────

@app.route("/calculate", methods=["GET", "POST"])
@login_required
def calculate_route():
    loc_data, _ = api_call(get_client().list_locations)
    locations = loc_data.get("locations", []) if loc_data else []
    result = None

    if request.method == "POST":
        try:
            data, err = api_call(
                get_client().calculate_route,
                origin_id=int(request.form["origin_id"]),
                dest_id=int(request.form["dest_id"]),
                weight_kg=float(request.form["weight_kg"]),
                volume_m3=float(request.form["volume_m3"]),
                is_fragile="is_fragile" in request.form,
                is_dangerous="is_dangerous" in request.form,
                is_liquid="is_liquid" in request.form,
                is_perishable="is_perishable" in request.form,
                is_crushable="is_crushable" in request.form,
                req_temp_control="req_temp_control" in request.form,
                strategy=request.form.get("strategy", "cheapest"),
            )
            if err:
                flash(err, "danger")
            else:
                result = data
        except (ValueError, KeyError) as e:
            flash(f"Ошибка в данных: {e}", "danger")

    return render_template("calculate_route.html", locations=locations, result=result)


# ── Менеджер: все заказы ──────────────────────────────────────────────

@app.route("/manage/orders")
@role_required("MANAGER", "ADMIN")
def manage_orders():
    data, err = api_call(get_client().list_all_orders)
    if err:
        flash(err, "danger")
        orders = []
    else:
        orders = data.get("orders", [])

    # Фильтр по статусу
    status_filter = request.args.get("status", "")
    if status_filter:
        orders = [o for o in orders if o.get("status") == status_filter]

    return render_template(
        "manage_orders.html", orders=orders,
        status_filter=status_filter,
    )


# ── Менеджер: управление заказом ──────────────────────────────────────

@app.route("/manage/orders/<order_id>", methods=["GET", "POST"])
@role_required("MANAGER", "ADMIN")
def manage_order(order_id: str):
    if request.method == "POST":
        new_status = request.form.get("new_status", "")
        comment = request.form.get("comment", "")
        data, err = api_call(
            get_client().update_status, order_id, new_status, comment or None,
        )
        if err:
            flash(err, "danger")
        else:
            flash(f"Статус обновлён → {STATUS_LABELS.get(new_status, new_status)}", "success")
        return redirect(url_for("manage_order", order_id=order_id))

    data, err = api_call(get_client().get_order, order_id)
    if err:
        flash(err, "danger")
        return redirect(url_for("manage_orders"))

    tracking_data, _ = api_call(get_client().get_tracking, order_id)
    events = tracking_data.get("events", []) if tracking_data else []

    # Определяем допустимые переходы
    current = data.get("status", "")
    transitions = {
        "CREATED": ["PROCESSING", "CANCELLED"],
        "PROCESSING": ["WAITING_DROP_OFF", "CANCELLED"],
        "WAITING_DROP_OFF": ["IN_TRANSIT", "CANCELLED"],
        "IN_TRANSIT": ["ARRIVED", "CANCELLED"],
        "ARRIVED": ["DELIVERED", "CANCELLED"],
    }
    allowed = transitions.get(current, [])

    return render_template(
        "manage_order.html", order=data, events=events, allowed=allowed,
    )


# ── Запуск ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)