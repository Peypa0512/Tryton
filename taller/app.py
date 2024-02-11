from datetime import datetime, date
import os
from functools import wraps
from flask import Flask, request, render_template,abort, session,redirect,url_for,g
from flask_tryton import Tryton
import psycopg2
import taller

app = Flask(__name__)
# conectarla a la bbdd
app.config['TRYTON_DATABASE'] = 'cars_db'
app.secret_key = 'ABCD,efg;1234;...'
tryton = Tryton(app, configure_jinja=True)
Marca = tryton.pool.get('taller.marca')
Modelo = tryton.pool.get('taller.modelo')
Coche = tryton.pool.get('taller.coche')
Party = tryton.pool.get('party.party')

WebUser = tryton.pool.get('web.user')
UserSession = tryton.pool.get('web.user.session')

def get_db_connection():
    conn = psycopg2.connect(database=app.config['TRYTON_DATABASE'], user='tryton', password='Admin,1$', host='localhost', port='5432')
    return conn


def login_required(func):
    @wraps(func)
    def wrapper(*arg, **kwargs):
        session_key = None
        if 'session_key' in session:
            session_key = session['session_key']
        g.user = UserSession.get_user(session_key)
        if not g.user:
            return redirect(url_for('login', next=request.path))
        return func(*arg, **kwargs)

    return wrapper


@app.route('/login', methods=['GET', 'POST'])
@tryton.transaction()
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username and password:
            user = WebUser.authenticate(username, password)
            if user:
                session['session_key'] = WebUser.new_session(user)
                session['username'] = user.email
                if user.party:
                    session['party'] = user.party.id
                    session['name'] = user.party.name
                next_ = request.form.get('next', None)
                if next_:
                    return redirect(next_)
                redirect('/')
            else:
                return 'Usuario Incorrecto'
    return render_template('login.html')


@app.route('/logout')
@tryton.transaction(readonly=False)
@login_required
def logout():
    if session['session_key']:
        user_sessions = UserSession.search([('key', '=', session['session_key'])])
        UserSession.delete(user_sessions)
        session.pop('session_key', None)
        session.pop('party', None)
        session.pop('username', None)
        session.pop('name', None)
    return redirect(request.referrer if request.referrer else url_for('index'))


@app.route('/signup', methods=['GET', 'POST'])
@tryton.transaction()
def signup():
    if request.method == 'POST':
        #creamos un nuevo tercero
        new_party = Party()
        new_party.name = request.form.get('name')
        new_party.save()
        #ahora le añadimos el resto del login
        user = WebUser()
        user.email = request.form.get('username')
        user.password = request.form.get('password')
        user.party = new_party
        user.save()
        return redirect(url_for('lista_coches'))
    terceros = Party.search([])
    return render_template('signup.html', terceros=terceros)




@app.route('/')
@tryton.transaction()
def lista_coches():
    marcas = Marca.search([])  # para que devuelva todos los registrospi
    return render_template('marca.html', marca=marcas)

@app.route('/marca/<marca_url>')
@tryton.transaction()
def lista_modelos(marca_url):
    modelo = Modelo.search([('marca', '=', marca_url)])  # nos devuelve la marca
    coche = Coche.search([('marca', '=', marca_url)])
    marcas = Marca.search([('name', '=', marca_url)])
    return render_template('modelo.html', mi_marcas=marcas[0], mi_modelo=modelo, mi_coche=coche)


@app.route('/comprar/<record("taller.modelo"):modelo>', methods=['POST', 'GET'])
@tryton.transaction()
def compra_coche(modelo):
    #para leer todos los terceros
    terceros = Party.search([])
    if request.method == 'POST':
        newCoche = Coche()
        newCoche.matricula = request.form.get('matricula', "")
        newCoche.propietario = int(request.form.get('terceros', 0))
        newCoche.marca = modelo.marca
        newCoche.modelo = modelo
        if session.get('party'):
            miTercero = Party(session.get('party'))
            newCoche.propietario = miTercero
        else:
            newCoche.propietario = int(request.form.get('propietario', 0))

        newCoche.save()
        return redirect(url_for('lista_modelos', marca_url=modelo.marca.name))

    return render_template('comprar_coche.html', modelo=modelo, tercero=terceros)


@app.route('/newMarca/', methods=['POST', 'GET'])
@tryton.transaction()
def add_marca():
    if request.method == 'POST':
        newMarca = Marca()
        newMarca.name = request.form.get('marca', "")
        newMarca.save()
        return redirect(url_for('lista_modelos'))
    return render_template('/')


@app.route('/newModel/<record("taller.marca"):marca>', methods=['POST', 'GET'])
@tryton.transaction()
def add_modelo(marca):
    if request.method == 'POST':
        newModelo = Modelo()
        newModelo.marca = marca
        newModelo.modelo = request.form.get('modelo', "")
        newModelo.combustible = request.form.get('combustible', "")
        newModelo.fecha_lanz = date.today()
        newModelo.save()
        return redirect(url_for('lista_coches', marca_url=marca.name))
    combustibles = Modelo.fields_get(['combustible'])['combustible']['selection']
    return render_template('newModel.html', mi_marcas=marca, mi_combustible=combustibles)


# @app.route('/marca/<marca_url>', methods=['GET', 'POST'])
# def exportar_registros(marca_url):
#     print('llega algo')
#     registros_seleccionados = request.form.getlist('registro_id')
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cursor.execute("SELECT matricula, marca, modelo, precio, fecha_matriculacion, fecha_baja FROM taller_coche WHERE id IN %s",
#                    (tuple(registros_seleccionados),))
#
#     registros = cursor.fetchall()
#     for registro in registros:
#             print('Marca: ', registro[1].rec_name)
#
#
#     return render_template('exportar_excel.html', registros=registros)
# @app.route('/marca/<marca_url>', methods=['GET', 'POST'])
# def seleccionar(marca_url):
#     registros_seleccionados = request.form.getlist('registro_id')
#     print('Registros :',registros_seleccionados)
#     return redirect('/export_excel', registros=' + '.join(registros_seleccionados))
#
# @app.route('/export_excel')
# def export_excel():
#
#     registros_seleccionados = request.args.get('registros').split(',')
#     print(registros_seleccionados)
#     # Aquí puedes realizar las operaciones necesarias para generar el archivo export_excel.html con los registros seleccionados
#     # Puedes pasar los registros seleccionados como argumento a la plantilla export_excel.html usando render_template
#     return render_template('exportar_excel.html', registros=registros_seleccionados)

@app.route('/marca/<marca_url>', methods=['GET', 'POST'])
def seleccionar(marca_url):
   # ids_seleccionados = request.form.getlist('checkbox')  # Obtener los IDs seleccionados desde el formulario

    # Usar los IDs para obtener el resto de los registros de la tabla

    # for id in ids_seleccionados:
    #     # Aquí debes implementar la lógica para obtener los registros de la tabla usando el ID
    #     # Puedes usar consultas a la base de datos o cualquier otro método que estés utilizando en tu aplicación
    #     print(id)
    #     # Ejemplo de cómo podrías obtener los campos marca, modelo, matrícula y precio de un registro
    #     marca = Coche.marca[id]
    #     modelo = Coche.modelo[id]
    #     matricula = Coche.matricula[id]
    #     precio = Coche.precio[id]
    #     print(marca, ',', modelo, ',', matricula, ',', precio)
    #     # Agregar los campos a la lista de registros
    #     registros.append({
    #         'id': id,
    #         'marca': marca,
    #         'modelo': modelo,
    #         'matricula': matricula,
    #         'precio': precio
    #     })
    #     print(registros)

    datos = request.json
    print(datos)
    return render_template('exportar_excel.html', datos=datos)


