from flask import Flask, render_template, request, redirect, url_for
from db import get_connection

app = Flask(__name__)

# HOME PAGE - Dashboard with summary statistics
@app.route('/')
def index():
    conn = get_connection()

    # Use RealDictCursor so results come back as dictionaries
    cur = conn.cursor(cursor_factory=__import__('psycopg2').extras.RealDictCursor)

    # Basic table counts for dashboard cars
    cur.execute("SELECT COUNT(*) AS total FROM car")
    total_cars = cur.fetchone()['total']

    cur.execute("SELECT COUNT(*) AS total FROM brand")
    total_brands = cur.fetchone()['total']

    cur.execute("SELECT COUNT(*) AS total FROM \"user\"")
    total_users = cur.fetchone()['total']

    cur.execute("SELECT COUNT(*) AS total FROM list")
    total_lists = cur.fetchone()['total']

    # Top 5 brands by number of cars, including stats
    cur.execute("""
        SELECT b.b_brandname, COUNT(c.c_carid) AS car_count,
            ROUND(AVG(c.c_price), 2) AS avg_price,
            MAX(c.c_horsepower) AS max_hp
        FROM brand b
        JOIN car c ON b.b_brandid = c.c_brandid
        GROUP BY b.b_brandname
        ORDER BY car_count DESC
        LIMIT 5
    """)
    top_brands = cur.fetchall()

    cur.close()
    conn.close()

    # Render dashboard template
    return render_template('index.html',
        total_cars=total_cars,
        total_brands=total_brands,
        total_users=total_users,
        total_lists=total_lists,
        top_brands=top_brands)

# CARS PAGE - Filtering, sorting, and listing cars
@app.route('/cars')
def cars():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=__import__('psycopg2').extras.RealDictCursor)

    # Read filter/sort parameters from URL query string
    brand_filter = request.args.get('brand', '')
    min_price = request.args.get('min_price', '')
    max_price = request.args.get('max_price', '')
    sort = request.args.get('sort', 'c_price')

    # Prevent SQL injection by restricting allowed sort columns
    allowed_sorts = ['c_price', 'c_horsepower', 'c_year', 'c_zerotosixty']
    if sort not in allowed_sorts:
        sort = 'c_price'

    # Base query
    query = """
        SELECT c.c_carid, b.b_brandname, c.c_model, c.c_year,
            c.c_enginesize, c.c_horsepower, c.c_torque,
            c.c_zerotosixty, c.c_price
        FROM car c
        JOIN brand b ON c.c_brandid = b.b_brandid
        WHERE 1=1
    """
    params = []

    # Apply filters dynamically
    if brand_filter:
        query += " AND LOWER(b.b_brandname) LIKE LOWER(%s)"
        params.append(f"%{brand_filter}%")
    if min_price:
        query += " AND c.c_price >= %s"
        params.append(min_price)
    if max_price:
        query += " AND c.c_price <= %s"
        params.append(max_price)

    # Sorting and limit
    query += f" ORDER BY {sort} DESC LIMIT 50"

    cur.execute(query, params)
    car_list = cur.fetchall()

    # Get list of all brands for dropdown filter
    cur.execute("SELECT b_brandname FROM brand ORDER BY b_brandname")
    brands = cur.fetchall()

    cur.close()
    conn.close()
    return render_template('cars.html', cars=car_list, brands=brands,
        brand_filter=brand_filter, min_price=min_price,
        max_price=max_price, sort=sort)


# USERS PAGE - View, add, and delete users
@app.route('/users')
def users():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=__import__('psycopg2').extras.RealDictCursor)

    # Show users and how many lists each one owns
    cur.execute("""
        SELECT u.u_userid, u.u_name, u.u_email,
            COUNT(l.l_listid) AS list_count
        FROM "user" u
        LEFT JOIN list l ON u.u_userid = l.l_userid
        GROUP BY u.u_userid, u.u_name, u.u_email
        ORDER BY u.u_userid
    """)
    user_list = cur.fetchall()

    cur.close()
    conn.close()
    return render_template('users.html', users=user_list)

@app.route('/users/add', methods=['POST'])
def add_user():
    # Add a new user from form submission
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO "user" (u_name, u_email, u_password)
        VALUES (%s, %s, %s)
    """, (name, email, password))

    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('users'))

@app.route('/users/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    # Delete a user by ID
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM \"user\" WHERE u_userid = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('users'))

# LISTS PAGE - View, add, delete lists
@app.route('/lists')
def lists():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=__import__('psycopg2').extras.RealDictCursor)

    # Show lists with aggregated stats
    cur.execute("""
        SELECT l.l_listid, l.l_listname, u.u_name,
            COUNT(li.li_listitemid) AS item_count,
            ROUND(AVG(c.c_price), 2) AS avg_price,
            MAX(c.c_horsepower) AS max_hp,
            MIN(c.c_zerotosixty) AS fastest_60
        FROM list l
        JOIN "user" u ON l.l_userid = u.u_userid
        LEFT JOIN listitem li ON l.l_listid = li.li_listid
        LEFT JOIN car c ON li.li_carid = c.c_carid
        GROUP BY l.l_listid, l.l_listname, u.u_name
        ORDER BY l.l_listid
    """)
    all_lists = cur.fetchall()

    # For dropdown when creating new lists
    cur.execute("SELECT u_userid, u_name FROM \"user\" ORDER BY u_name")
    all_users = cur.fetchall()

    cur.close()
    conn.close()
    return render_template('lists.html', lists=all_lists, users=all_users)

@app.route('/lists/add', methods=['POST'])
def add_list():
    # Create a new list for a user
    user_id = request.form['user_id']
    list_name = request.form['list_name']

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("INSERT INTO list (l_userid, l_listname) VALUES (%s, %s)",
        (user_id, list_name))
    
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('lists'))

@app.route('/lists/delete/<int:list_id>', methods=['POST'])
def delete_list(list_id):
    # Delete a list by ID
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM list WHERE l_listid = %s", (list_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('lists'))

# LIST ITEMS - View, add, update, delete items inside a list
@app.route('/lists/<int:list_id>')
def list_detail(list_id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=__import__('psycopg2').extras.RealDictCursor)

    # Get list name and owner
    cur.execute("""
        SELECT l.l_listname, u.u_name
        FROM list l JOIN "user" u ON l.l_userid = u.u_userid
        WHERE l.l_listid = %s
    """, (list_id,))
    list_info = cur.fetchone()

    # Get all items in the list
    cur.execute("""
        SELECT li.li_listitemid, b.b_brandname, c.c_model, c.c_year,
            c.c_price, c.c_horsepower, c.c_zerotosixty,
            li.li_notes, li.li_priority
        FROM listitem li
        JOIN car c ON li.li_carid = c.c_carid
        JOIN brand b ON c.c_brandid = b.b_brandid
        WHERE li.li_listid = %s
        ORDER BY li.li_priority, c.c_price DESC
    """, (list_id,))
    items = cur.fetchall()

    # Stats for the list (average price, fastest 0-60, etc.)
    cur.execute("""
        SELECT COUNT(*) AS total,
            ROUND(AVG(c.c_price), 2) AS avg_price,
            MAX(c.c_horsepower) AS max_hp,
            MIN(c.c_zerotosixty) AS fastest_60,
            ROUND(AVG(c.c_zerotosixty), 2) AS avg_60
        FROM listitem li
        JOIN car c ON li.li_carid = c.c_carid
        WHERE li.li_listid = %s
    """, (list_id,))
    stats = cur.fetchone()

    # Cars not already in the list (for dropdown)
    cur.execute("""
        SELECT c.c_carid, b.b_brandname || ' ' || c.c_model || ' (' || c.c_year || ')' AS car_label
        FROM car c JOIN brand b ON c.c_brandid = b.b_brandid
        WHERE c.c_carid NOT IN (
            SELECT li_carid FROM listitem WHERE li_listid = %s
        )
        ORDER BY b.b_brandname, c.c_model
    """, (list_id,))
    available_cars = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('list_detail.html', list_info=list_info,
        items=items, stats=stats,
        available_cars=available_cars, list_id=list_id)

@app.route('/lists/<int:list_id>/add_item', methods=['POST'])
def add_list_item(list_id):
    # Add a new car to a list
    car_id = request.form['car_id']
    notes = request.form.get('notes', '')
    priority = request.form.get('priority', 'Considering')

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO listitem (li_listid, li_carid, li_notes, li_priority)
        VALUES (%s, %s, %s, %s)
    """, (list_id, car_id, notes, priority))

    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('list_detail', list_id=list_id))

@app.route('/lists/<int:list_id>/update_item/<int:item_id>', methods=['POST'])
def update_list_item(list_id, item_id):
    # Update notes/priority for a list item
    notes = request.form.get('notes', '')
    priority = request.form.get('priority', 'Considering')

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE listitem SET li_notes = %s, li_priority = %s
        WHERE li_listitemid = %s
    """, (notes, priority, item_id))

    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('list_detail', list_id=list_id))

@app.route('/lists/<int:list_id>/delete_item/<int:item_id>', methods=['POST'])
def delete_list_item(list_id, item_id):
    # Remove a car from a list
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM listitem WHERE li_listitemid = %s", (item_id,))

    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('list_detail', list_id=list_id))

# Run app
if __name__ == '__main__':
    app.run(debug=True)