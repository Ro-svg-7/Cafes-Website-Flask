from flask import Flask, render_template, request, jsonify, redirect, url_for, make_response, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Boolean, inspect, select
from sqlalchemy.sql.expression import func
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'my-secret-key'

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    print(user_id)
    user_found = db.session.execute(db.select(Users).where(Users.id == user_id)).scalar()
    if user_found:
        print("User loaded successfully.")
        return user_found
    print("User not loaded")
    return abort(404)

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

    reports = relationship("Reports", back_populates="cafe")

    def to_dict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs} # type: ignore

class Users(UserMixin, db.Model):

    def __init__(self, email: str, password: str, name:str):
        self.email = email
        self.password = password
        self.name = name

    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(250), nullable=False)
    name: Mapped[str] = mapped_column(String(250), nullable=False)

    reports = relationship("Reports", back_populates="user")
    
class Reports(db.Model):

    def __init__(self, user_id: int, cafe_id: int):
        self.user_id = user_id
        self.cafe_id = cafe_id

    __tablename__ = "reports"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    cafe_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("cafe.id"))
    user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))

    user = relationship("Users", back_populates="reports")
    cafe = relationship("Cafe", back_populates="reports")

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


@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "")
        password = request.form.get("password", "")
        name = request.form.get("name", "")

        exisiting_user = db.session.execute(
            select(Users).where(Users.email == email)
        ).scalar()

        if exisiting_user:
            return "User already exists. Please log in instead."
        
        hashed_password = generate_password_hash(password)

        new_user = Users(
            email = email,
            password = hashed_password,
            name = name
        )
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        return redirect(url_for("cafes_page"))
    return render_template("register.html")
    
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "")
        password = request.form.get("password", "")

        user = db.session.execute(
            select(Users).where(Users.email == email)
        ).scalar()

        if not user:
            return "User Not Found."
        
        if not check_password_hash(user.password, password):
            return "Wrong Password. Please Try Again."

        login_user(user)
        return redirect(url_for("cafes_page"))
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("homepage"))


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
            has_toilet=request.form.get("has_toilet") == "on", # type: ignore
            has_wifi=request.form.get("has_wifi") == "on", # type: ignore
            has_sockets=request.form.get("has_sockets") == "on", # type: ignore
            can_take_calls=request.form.get("can_take_calls") == "on", # type: ignore
            coffee_price=request.form.get("coffee_price") # type: ignore
        )

        db.session.add(new_cafe)
        db.session.commit()

        return redirect(url_for("cafes_page"))

    return render_template("add.html")

#HTTP DELETE - Report Record 
@app.route("/report-closed/<int:cafe_id>", methods=["POST"])
@login_required
def report_closed(cafe_id):
    cafe = db.session.get(Cafe, cafe_id)

    if not cafe:
        return "Cafe not found", 404
   
    existing_report = db.session.execute(
        select(Reports).where(
            Reports.user_id == current_user.id, 
            Reports.cafe_id == cafe_id
        )
    ).scalar()

    if existing_report:
        return redirect(url_for("cafe_details", cafe_id=cafe_id))
    
    new_report = Reports(
        user_id = current_user.id,
        cafe_id = cafe_id
    )

    db.session.add(new_report)

    report_count = db.session.execute(
        select(Reports.user_id).where(Reports.cafe_id == cafe_id)
        .distinct()
    ).all()

    if len(report_count) >= 3:
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
