from datetime import datetime, timedelta

from db_models.payment import Payment
from flask import Flask, jsonify, render_template, request, send_file
from payments.pix import Pix
from repository.database import db

app = Flask(__name__, template_folder="static/templates")

app.config["SECRET_KEY"] = "your_secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"

db.init_app(app)


@app.shell_context_processor
def shell_context():
    # Disponibiliza o banco e os modelos no flask shell.
    return {"db": db, "Payment": Payment}


@app.route("/payments/pix", methods=["POST"])
def create_payment_pix():
    data = request.get_json()
    # validações
    if "value" not in data:
        return jsonify({"message": "Invalid value"}), 400

    expiration_date = datetime.now() + timedelta(minutes=30)  # calculo para expiração

    new_payment = Payment(value=data["value"], expiration_date=expiration_date)

    pix_object = Pix()
    data_payment_pix = pix_object.create_payment()
    # o identificador do pagamento
    new_payment.bank_payment_id = data_payment_pix["bank_payment_id"]
    # o identificador do qr-code
    new_payment.qr_code = data_payment_pix["qr_code_path"]

    db.session.add(new_payment)
    db.session.commit()

    return jsonify(
        {
            "message": "The payment has been created",
            "payment": new_payment.to_dict(),
        }  # new_payment_.to_dict() visualizar os dados em JSON
    )


# Rota para visualizar um qr code de dado pagamento
@app.route("/payments/pix/qr_code/<file_name>", methods=["GET"])
def get_image(file_name):
    return send_file(f"static/img/{file_name}.png", mimetype="image/png")


@app.route("/payments/pix/confirmation", methods=["POST"])
def create_payment_pix_confirmation():
    return jsonify({"message": "The payment has been confirmed"})


@app.route("/payments/pix/<int:payment_id>", methods=["GET"])
def payment_pix_page(payment_id):
    # requisição para rota que sempre irá retornar esse template fixo
    payment = Payment.query.get(payment_id)

    # através do id desse banco que formos mandar teremos informações como, o id de transação
    # e o valor da compra

    return render_template(
        "payment.html",
        payment_id=payment.id,
        value=payment.value,
        host="http://localhost:5000",
        qr_code=payment.qr_code,
    )


if __name__ == "__main__":
    app.run(debug=True)
