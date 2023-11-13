import pymysql
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import time
import datetime
import secrets

# Membuat server Flask
app = Flask(__name__)

app.secret_key = secrets.token_hex(16)
# Koneksi ke database MySQL
db = pymysql.connect(
	host="localhost",
	user="root",
	passwd="",
	database="db-square-root"
)

    
    
@app.route('/home')
def index():
    return render_template('index.html')


@app.route('/', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = db.cursor()
        cursor.execute('SELECT * FROM accounts WHERE username = % s AND password = % s', (username, password, ))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account[0]  # Assuming 'id' is the first column
            session['username'] = account[1]  # Assuming 'username' is the second column
            msg = 'Logged in successfully !'
            return render_template('index.html', msg = msg)
        else:
            msg = 'Incorrect username / password !'
    return render_template('login.html', msg = msg)
 

@app.route('/register', methods =['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = db.cursor()
        cursor.execute('SELECT * FROM accounts WHERE username = % s', (username, ))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists !'
        elif not username or not password:
            msg = 'Please fill out the form !'
        else:
            cursor = db.cursor()
            cursor.execute('INSERT INTO accounts VALUES (NULL, % s, % s)', (username, password))
            db.commit()
            msg = 'You have successfully registered !'
    elif request.method == 'POST':
        msg = 'Please fill out the form !'
    return render_template('register.html', msg = msg)

    

# Menggunakan API
@app.route('/api/hitung-akar-kuadrat-api', methods=['POST'])
def hitung_akar_kuadrat_api():
    cursor = None  
    try:
        jenis ='API'
        data = request.get_json()
        angka = data.get('angka')  # Use get() to safely access the 'angka' key

        if angka is None or angka <0:
            return jsonify({'error': 'Angka tidak boleh kosong dan atau kurang dari 0'}), 400

     # Your code to calculate the square root
        tebakan = angka / 2
        epsilon = 0.00001

        # Catat waktu mulai perhitungan
        start_time = time.perf_counter()  # Waktu dalam detik dengan presisi yang lebih tinggi

        while True:
            akar_tebakan = 0.5 * (tebakan + angka / tebakan)
            error = abs(akar_tebakan - tebakan)

            if error < epsilon:
                break

            tebakan = akar_tebakan

        # Hitung waktu selesai perhitungan
        end_time = time.perf_counter()  # Waktu dalam detik dengan presisi yang lebih tinggi
        waktu_penghitungan = (end_time - start_time)  # Dalam detik

        # Format the time result to match PHP
        waktu_penghitungan = round(waktu_penghitungan, 9)  # Round to 9 decimal places

        # Simpan hasil perhitungan ke database MySQL
        cursor = db.cursor()
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        user_id = session.get('id')

        # Insert data ke tabel
        cursor.execute("INSERT INTO logs (input, hasil, waktu, jenis, created_at, updated_at, user_id) VALUES (%s, %s, %s, %s, NOW(), NOW(), %s)",
        (angka, akar_tebakan, waktu_penghitungan, jenis, user_id))
        db.commit()

        return jsonify({'input_angka': angka, 'hasil': akar_tebakan, 'waktu_penghitungan': waktu_penghitungan})
    
    except Exception as e:
        if cursor:
            db.rollback()  # rollback jika ada error
            cursor.close()
        print(f"Database error: {str(e)}")
        return jsonify({'error': 'Terjadi kesalahan'}), 500

# Menggunakan Stored Procedure 
@app.route('/api/hitung-akar-kuadrat-plsql', methods=['POST'])
def hitung_akar_kuadrat_plsql():
    try:
        jenis = 'SP-SQL'
        data = request.get_json()
        angka = data['angka']
        user_id = session.get('id')
        
        if angka is None or angka <0:
            return jsonify({'error': 'Angka tidak boleh kosong dan atau kurang dari 0'}), 400

        cursor = db.cursor()
        cursor.callproc('square_root', (angka, 0, 0, user_id))  # Memanggil stored procedure dengan parameter input, output output, dan output timeoutput
        db.commit()
       
        # convert data
        logs = [{'input': row[0],'hasil': row[1], 'waktu-penghitungan': row[2]} for row in data]
        formatted_data = {
        "input_angka": logs[0]['input'],  
        "hasil": logs[0]['hasil'],  
        "waktu_penghitungan": logs[0]['waktu-penghitungan'], 
        "user_id": user_id
        }

        return jsonify(formatted_data)


    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/log', methods=['GET'])
def log():
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT logs.input, logs.hasil, logs.waktu, logs.jenis, accounts.username
            FROM logs
            JOIN accounts ON logs.user_id = accounts.id
            ORDER BY logs.id DESC
        """)
        data = cursor.fetchall()
        cursor.close()

        # Convert data
        logs = [{'input': row[0], 'hasil': row[1], 'waktu': row[2], 'jenis': row[3], 'username': row[4]} for row in data]

        # Passing data to the template
        return render_template('log.html', logs=logs)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5010, debug=True)

