import datetime

from flask import Blueprint
from flask import render_template, request, redirect, url_for, jsonify
from flask import g
from flask.json.tag import TagDict

from . import db

bp = Blueprint("pets", "pets", url_prefix="")

def format_date(d):
    if d:
        d = datetime.datetime.strptime(d, '%Y-%m-%d')
        v = d.strftime("%a - %b %d, %Y")
        return v
    else:
        return None

@bp.route("/search/<field>/<value>")
def search(field, value):
    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute("select id from tag where name = ?", [value]);
    tag_id = cursor.fetchone()[0]
    cursor.execute("select p.id, p.name, p.bought, p.sold, p.species from pet p, tags_pets t where t.tag = ? and t.pet = p.id", [tag_id])
    pets = cursor.fetchall()
    return render_template("search.html", pets = pets)

@bp.route("/")
def dashboard():
    conn = db.get_db()
    cursor = conn.cursor()
    oby = request.args.get("order_by", "id") # TODO. This is currently not used. 
    order = request.args.get("order", "asc")
    if order == "asc":
        cursor.execute(f"select p.id, p.name, p.bought, p.sold, s.name from pet p, animal s where p.species = s.id order by p.{oby}")
    else:
        cursor.execute(f"select p.id, p.name, p.bought, p.sold, s.name from pet p, animal s where p.species = s.id order by p.{oby} desc")
    pets = cursor.fetchall()
    return render_template('index.html', pets = pets, order="desc" if order=="asc" else "asc")


@bp.route("/<pid>")
def pet_info(pid): 
    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute("select p.name, p.bought, p.sold, p.description, s.name from pet p, animal s where p.species = s.id and p.id = ?", [pid])
    pet = cursor.fetchone()
    cursor.execute("select t.name from tags_pets tp, tag t where tp.pet = ? and tp.tag = t.id", [pid])
    tags = (x[0] for x in cursor.fetchall())
    name, bought, sold, description, species = pet
    data = dict(id = pid,
                name = name,
                bought = format_date(bought),
                sold = format_date(sold),
                description = description, #TODO Not being displayed
                species = species,
                tags = tags)
    return render_template("petdetail.html", **data)

@bp.route("/<pid>/edit", methods=["GET", "POST"])
def edit(pid):
    conn = db.get_db()
    cursor = conn.cursor()
    if request.method == "GET":
        cursor.execute("select p.name, p.bought, p.sold, p.description, s.name from pet p, animal s where p.species = s.id and p.id = ?", [pid])
        pet = cursor.fetchone()
        cursor.execute("select t.name from tags_pets tp, tag t where tp.pet = ? and tp.tag = t.id", [pid])
        tags = (x[0] for x in cursor.fetchall())
        name, bought, sold, description, species = pet
        data = dict(id = pid,
                    name = name,
                    bought = format_date(bought),
                    sold = format_date(sold),
                    description = description,
                    species = species,
                    tags = tags)
        return render_template("editpet.html", **data)
    elif request.method == "POST":
        description = request.form.get('description')
        sold = request.form.get("sold")
        if(sold):
            sold = datetime.datetime.now().strftime("%Y-%m-%d")
        cursor.execute("update pet set description=?, sold=? where id=?", [description, sold, pid])
        conn.commit()
        return redirect(url_for("pets.pet_info", pid=pid), 302)
        
    



