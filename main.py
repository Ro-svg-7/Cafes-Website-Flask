from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean, inspect, select
from sqlalchemy.sql.expression import func

app = Flask(__name__)

#Creating DataBase
class Base(DeclarativeBase):
    pass
#Connect to DataBase
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

#Cafe Table Config
class Cafe(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reports: Mapped[int] = mapped_column(Integer, default=0)
    name: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    map_url: Mapped[str] = mapped_column(String(250), unique=False, nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), unique=False, nullable=False)
    location: Mapped[str] = mapped_column(String(250), unique=False, nullable=False)
    seats: Mapped[str] = mapped_column(String(250), nullable=False)
    has_toilet: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_wifi: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_sockets: Mapped[bool] = mapped_column(Boolean, nullable=False)
    can_take_calls: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False)
    coffee_price: Mapped[str] = mapped_column(String(250), nullable=True)

    def to_dict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs} # type: ignore
with app.app_context():

    db.create_all()

    try:
        db.session.execute(db.text("ALTER TABLE cafe ADD COLUMN reports INTEGER DEFAULT 0"))
    except:
        pass

    try:
        db.session.execute(db.text("ALTER TABLE cafe ADD COLUMN is_closed BOOLEAN DEFAULT 0"))
    except:
        pass

    db.session.commit()


@app.route("/")
def homepage():
    return render_template("index.html")

#HTTP GET - Read Record
@app.route("/random", methods=["GET"])
def get_random_cafe():
    result = db.session.execute(db.select(Cafe).order_by(func.random()))
    random_cafe = result.scalar()

    if random_cafe:
        return jsonify(cafe=random_cafe.to_dict())
    return jsonify(error={"Not Found": "No Cafe in the Database."}), 404

@app.route("/cafes", methods=["GET"])
def cafes_page():
    print("CAFES ROUTE HIT 🔥")
    cafes = db.session.execute(db.select(Cafe)).scalars().all()
    print(f"DEBUG: Found {len(cafes)} cafes in DB")
    return render_template("cafes.html", cafes=cafes)

@app.route("/cafe/<int:cafe_id>", methods=["GET"])
def cafe_details(cafe_id):
    cafe = db.session.get(Cafe, cafe_id)
    return render_template("cafe_home.html", cafe=cafe)
#HTTP POST - Add Record
@app.route("/cafes/add", methods=["GET", "POST"])
def add_cafe():
    if request.method == "POST":
        new_cafe = Cafe(
            name=request.form.get("name"), # type: ignore
            map_url=request.form.get("map_url"), # type: ignore
            img_url=request.form.get("img_url"), # type: ignore
            location=request.form.get("location"), # type: ignore
            seats=request.form.get("seats"), # type: ignore
            has_toilet=request.form.get("has_toilet") == "true" or request.form.get("has_wifi") == "on", # type: ignore
            has_wifi=request.form.get("has_wifi") == "true", # type: ignore
            has_sockets=request.form.get("has_sockets") == "true", # type: ignore
            can_take_calls=request.form.get("can_take_calls") == "true", # type: ignore
            coffee_price=request.form.get("coffee_price") # type: ignore+
        )

        db.session.add(new_cafe)
        db.session.commit()

        return redirect(url_for("cafes_page"))

    return render_template("add.html")

#HTTP DELETE - Report Record 
@app.route("/report-closed/<int:cafe_id>", methods=["POST"])
def report_closed(cafe_id):
    cafe = db.session.get(Cafe, cafe_id)

    if not cafe:
        return "Cafe not found", 404
    
    cafe.reports += 1

    #Threshold Logic
    if cafe.reports >= 3:
        cafe.is_closed = True
    
    db.session.commit()

    return redirect(url_for("cafe_details", cafe_id=cafe_id))

@app.route("/update-price/<int:cafe_id>", methods=["POST"])
def update_price(cafe_id):
    #Fetching new price
    new_price = request.form.get("new_price")

    cafe = db.session.get(Cafe, cafe_id)

    if cafe:
        cafe.coffee_price = new_price # type: ignore
        db.session.commit()

        return jsonify(success="Successfullt updated the price.", cafe=cafe.to_dict()),200
    else:
        return jsonify(error={"Not Found": "Sorry, a cafe with that id was not found in the database."}), 404
    
if __name__ == "__main__":
    app.run(debug=True)
