from flask import Flask, jsonify, request
from config import PORT
from database import initialize_database, get_customers, get_customer, get_accounts, get_loans, get_loan, create_loan

app = Flask(__name__)

@app.get("/")
def home():
    return jsonify(success=True, system="Bank API", message="Bank API is running")

@app.get("/api/health")
def health():
    return jsonify(success=True, system="Bank Financing API", status="online")

@app.get("/api/customers")
def customers():
    data = get_customers()
    return jsonify(success=True, count=len(data), customers=data)

@app.get("/api/accounts")
def accounts():
    data = get_accounts()
    return jsonify(success=True, count=len(data), accounts=data)

@app.get("/api/loans")
def loans():
    data = get_loans()
    return jsonify(success=True, count=len(data), loans=data)

@app.get("/api/loans/<int:loan_id>")
def loan(loan_id):
    data = get_loan(loan_id)
    if not data:
        return jsonify(success=False, message="Loan not found"), 404
    return jsonify(success=True, loan=data)

@app.post("/api/loans")
def create_loan_api():
    data = request.get_json(silent=True) or {}
    required = ["customer_id", "amount", "months"]
    missing = [f for f in required if data.get(f) in (None, "")]
    if missing:
        return jsonify(success=False, message="Missing required fields", fields=missing), 400

    try:
        customer_id = int(data["customer_id"])
        amount = float(data["amount"])
        months = int(data["months"])
        car_id = int(data["car_id"]) if data.get("car_id") else None
    except (ValueError, TypeError):
        return jsonify(success=False, message="Invalid numeric values"), 400

    if amount <= 0 or months <= 0:
        return jsonify(success=False, message="Amount and months must be greater than zero"), 400

    customer = get_customer(customer_id)
    if not customer:
        return jsonify(success=False, message="Customer not found"), 404

    status = "Approved" if amount <= 100000 and months <= 60 else "Rejected"
    loan_id, monthly_payment = create_loan(
        customer_id, car_id, data.get("car_name", ""), amount, months, status
    )

    return jsonify(
        success=(status == "Approved"),
        message=("Loan approved successfully" if status == "Approved"
                 else "Loan rejected according to bank policy"),
        loan={
            "id": loan_id,
            "customer_id": customer_id,
            "customer_name": customer["name"],
            "car_id": car_id,
            "car_name": data.get("car_name", ""),
            "amount": amount,
            "months": months,
            "monthly_payment": monthly_payment,
            "status": status
        }
    ), 201

if __name__ == "__main__":
    initialize_database()
    app.run(host="0.0.0.0", port=PORT)
