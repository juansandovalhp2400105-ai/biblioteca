from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
from biblioteca import Biblioteca, Libro, Usuario, Prestamo, Bibliotecario
from datetime import datetime
from functools import wraps
import json

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'  
biblioteca = Biblioteca()
bibliotecario = Bibliotecario(id_bibliotecario="BIB001", nombre="Bibliotecario Principal")

def requiere_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Debes iniciar sesión primero.', 'error')
            return redirect(url_for('login'))
        
        if session.get('role') != 'admin':
            flash('Acceso denegado. No tienes permisos de administrador.', 'error')
            return redirect(url_for('user_view'))
            
        user_id = session.get('user_id')
        usuario = next((u for u in biblioteca.usuarios if str(u.id_usuario) == str(user_id)), None)
        
        if not usuario or usuario.nombre.lower() not in ['noel', 'isabela', 'sandoval']:
            session.pop('role', None)
            flash('Acceso denegado. No tienes permisos de administrador.', 'error')
            return redirect(url_for('user_view'))
            
        return f(*args, **kwargs)
    return decorated_function

def requiere_usuario(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Debes iniciar sesión primero.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('user_view'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        contrasena = request.form.get('contrasena')
        
        usuario = next((u for u in biblioteca.usuarios if u.nombre.lower() == nombre.lower()), None)
        
        if usuario and usuario.contrasena == contrasena:
            session['user_id'] = usuario.id_usuario
            session['role'] = 'admin' if usuario.nombre.lower() in ['noel', 'isabela', 'sandoval'] else 'usuario'
            
            if session['role'] == 'admin':
                flash(f'Bienvenido administrador, {usuario.nombre}!', 'success')
                return redirect(url_for('manejar_libros'))
            flash(f'Bienvenido, {usuario.nombre}!', 'success')
            return redirect(url_for('user_view'))
        else:
            flash('Usuario o contraseña incorrectos', 'error')
    return render_template('login.html')

@app.route('/registro_usuario_publico', methods=['GET', 'POST'])
def registro_usuario_publico():
    if request.method == 'POST':
        data = request.form.to_dict()
        
        if any(u.nombre.lower() == data['nombre'].lower() for u in biblioteca.usuarios):
            flash('El nombre de usuario ya existe', 'error')
            return redirect(url_for('registro_usuario_publico'))
     
        if any(u.email == data['email'] for u in biblioteca.usuarios):
            flash('El email ya está registrado', 'error')
            return redirect(url_for('registro_usuario_publico'))
            
        nuevo_id = str(max([int(u.id_usuario) for u in biblioteca.usuarios] + [0]) + 1)
        
        nuevo_usuario = Usuario(
            id_usuario=nuevo_id,
            nombre=data['nombre'],
            email=data['email'],
            contrasena=data['contrasena'],
            rol='usuario'
        )
        biblioteca.registrar_usuarios(nuevo_usuario)
        guardar_datos()
        flash('Usuario registrado exitosamente. Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('login'))
    return render_template('registro_usuario_publico.html')

@app.route('/libros', methods=['GET', 'POST'])
@requiere_admin
def manejar_libros():
    if request.method == 'POST':
        data = request.form.to_dict()
        nuevo_libro = Libro(
            titulo=data['titulo'],
            autor=data['autor'],
            isbn=str(data['isbn']),
            editorial=data['editorial'],
            año_publicacion=data['año_publicacion']
        )
        bibliotecario.añadir_libro(biblioteca, nuevo_libro)
        guardar_datos()
        flash(f'Libro "{nuevo_libro.titulo}" registrado exitosamente', 'success')
        return redirect(url_for('manejar_libros'))
    else:
        return render_template("libros.html", libros=biblioteca.libros)

@app.route('/usuarios', methods=['GET', 'POST'])
@requiere_admin
def manejar_usuarios():
    if request.method == 'POST':
        data = request.form.to_dict()
        # Validar que el ID no exista
        if any(u.id_usuario == str(data['id_usuario']) for u in biblioteca.usuarios):
            flash('El ID de usuario ya existe', 'error')
            return redirect(url_for('manejar_usuarios'))
        nuevo_usuario = Usuario(
            id_usuario=str(data['id_usuario']),
            nombre=data['nombre'],
            email=data['email'],
            contrasena=data.get('contrasena', ''),
            rol=data.get('rol', 'usuario')
        )
        biblioteca.registrar_usuarios(nuevo_usuario)
        guardar_datos()
        flash('Usuario registrado exitosamente', 'success')
        return redirect(url_for('manejar_usuarios'))
    else:
        return render_template('usuarios.html', usuarios=biblioteca.usuarios)

@app.route('/prestamos', methods=['GET', 'POST'])
@requiere_admin
def gestionar_prestamos():
    if request.method == 'POST':
        data = request.form.to_dict()
        id_usuario = str(data['id_usuario'])
        isbn = str(data['isbn'])
        usuario = next((u for u in biblioteca.usuarios if str(u.id_usuario) == id_usuario), None)
        libro = next((l for l in biblioteca.libros if str(l.isbn) == isbn), None)

        if not usuario or not libro:
            flash('Usuario o libro no encontrado', 'error')
            return redirect(url_for('gestionar_prestamos'))

        if 'fecha_prestamo' in data:
            if not libro.disponible:
                flash(f'El libro "{libro.titulo}" ya está prestado', 'error')
                return redirect(url_for('gestionar_prestamos'))

            fecha_prestamo = datetime.strptime(data['fecha_prestamo'], '%Y-%m-%d')
            fecha_devolucion = datetime.strptime(data['fecha_devolucion'], '%Y-%m-%d')  # Corregido para usar fecha_devolucion
            usuario.prestar_libro(libro)
            nuevo_prestamo = Prestamo(
                id_prestamo=len(biblioteca.prestamos) + 1,
                libro=libro,
                usuario=usuario,
                fecha_prestamo=fecha_prestamo,
                fecha_devolucion=fecha_devolucion
            )
            biblioteca.prestamos.append(nuevo_prestamo)
            flash(f'Libro "{libro.titulo}" prestado exitosamente a {usuario.nombre}', 'success')
        else:
            prestamo = next((p for p in biblioteca.prestamos if
                            str(p.libro.isbn) == isbn and str(p.usuario.id_usuario) == id_usuario), None)
            if not prestamo:
                flash(f'El libro "{libro.titulo}" no está prestado por {usuario.nombre}', 'error')
                return redirect(url_for('gestionar_prestamos'))
            usuario.devolver_libro(libro)
            biblioteca.prestamos.remove(prestamo)
            flash(f'Libro "{libro.titulo}" devuelto exitosamente por {usuario.nombre}', 'success')

        guardar_datos()
        return redirect(url_for('gestionar_prestamos'))
    else:
        return render_template('prestamos.html', usuarios=biblioteca.usuarios, libros=biblioteca.libros,
                               prestamos=biblioteca.prestamos)


@app.route('/user')
@requiere_usuario
def user_view():
    user_id = session.get('user_id')
    return render_template('user.html', libros=biblioteca.libros, prestamos=biblioteca.prestamos, user_id=user_id)


@app.route('/eliminar_libro/<string:isbn>', methods=['POST'])
@requiere_admin
def eliminar_libro(isbn):
    libro = next((l for l in biblioteca.libros if str(l.isbn) == isbn), None)
    if libro:
        biblioteca.libros.remove(libro)
        guardar_datos()
        flash(f'Libro "{libro.titulo}" eliminado exitosamente', 'success')
    else:
        flash('Libro no encontrado', 'error')
    return redirect(url_for('manejar_libros'))

@app.route('/eliminar_usuario/<string:id_usuario>', methods=['POST'])
@requiere_admin
def eliminar_usuario(id_usuario):
    usuario = next((u for u in biblioteca.usuarios if str(u.id_usuario) == id_usuario), None)
    if usuario:
        biblioteca.usuarios.remove(usuario)
        guardar_datos()
        flash(f'Usuario "{usuario.nombre}" eliminado exitosamente', 'success')
    else:
        flash('Usuario no encontrado', 'error')
    return redirect(url_for('manejar_usuarios'))

@app.route('/cerrar_sesion', methods=['GET', 'POST'])
def cerrar_sesion():
    session.clear()
    flash('Sesión cerrada', 'success')
    return redirect(url_for('login'))

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        data = request.form.to_dict()
        if any(u.email == data['email'] for u in biblioteca.usuarios):
            flash('El email ya está registrado', 'error')
            return redirect(url_for('registro'))
        nuevo_usuario = Usuario(
            id_usuario=str(len(biblioteca.usuarios)+1),
            nombre=data['nombre'],
            email=data['email'],
            contrasena=data['contrasena'],
            rol=data['rol']
        )
        biblioteca.registrar_usuarios(nuevo_usuario)
        guardar_datos()
        flash('Registro exitoso. Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('login'))
    return render_template('registro.html')

def guardar_datos():
    with open('datos.json', 'w') as f:
        datos = {
            'libros': [libro.__dict__ for libro in biblioteca.libros],
            'usuarios': [usuario.__dict__ for usuario in biblioteca.usuarios],
            'prestamos': [{
                'id_prestamo': prestamo.id_prestamo,
                'libro': prestamo.libro.__dict__,
                'usuario': prestamo.usuario.__dict__,
                'fecha_prestamo': prestamo.fecha_prestamo.strftime('%Y-%m-%d'),
                'fecha_devolucion': prestamo.fecha_devolucion.strftime('%Y-%m-%d')
            } for prestamo in biblioteca.prestamos]
        }
        json.dump(datos, f, indent=4, default=str)

def cargar_datos():
    try:
        with open('datos.json', 'r') as f:
            contenido = f.read().strip()
            if not contenido:
                return
            datos = json.loads(contenido)

            for libro_data in datos.get('libros', []):
                if not datos_completos_libro(libro_data):
                    continue
                disponible = libro_data.pop('disponible', True)
                libro = Libro(**libro_data)
                libro.disponible = disponible
                biblioteca.libros.append(libro)

            for usuario_data in datos.get('usuarios', []):
                usuario_data.pop('libro_Prestados', None)
                usuario_data.pop('libros_prestados', None)
                usuario_data.setdefault('contrasena', '')
                usuario_data.setdefault('rol', 'usuario')
                if not datos_completos_usuario(usuario_data):
                    if all(k in usuario_data and usuario_data[k] for k in ['id_usuario', 'nombre', 'email']):
                        usuario_data['contrasena'] = usuario_data.get('contrasena', '')
                        usuario_data['rol'] = usuario_data.get('rol', 'usuario')
                    else:
                        continue
                usuario = Usuario(
                    id_usuario=usuario_data['id_usuario'],
                    nombre=usuario_data['nombre'],
                    email=usuario_data['email'],
                    contrasena=usuario_data.get('contrasena', ''),
                    rol=usuario_data.get('rol', 'usuario')
                )
                biblioteca.usuarios.append(usuario)

            for prestamo_data in datos.get('prestamos', []):
                libro_data = prestamo_data['libro']
                usuario_data = prestamo_data['usuario']
                libro = next((l for l in biblioteca.libros if str(l.isbn) == str(libro_data['isbn'])), None)
                usuario = next((u for u in biblioteca.usuarios if str(u.id_usuario) == str(usuario_data['id_usuario'])), None)

                if libro and usuario:
                    prestamo = Prestamo(
                        id_prestamo=prestamo_data['id_prestamo'],
                        libro=libro,
                        usuario=usuario,
                        fecha_prestamo=datetime.strptime(prestamo_data['fecha_prestamo'], '%Y-%m-%d'),
                        fecha_devolucion=datetime.strptime(prestamo_data['fecha_devolucion'], '%Y-%m-%d')
                    )
                    biblioteca.prestamos.append(prestamo)
    except (FileNotFoundError, json.JSONDecodeError):
        pass

def datos_completos_libro(libro_data):
    return all(k in libro_data and libro_data[k] for k in ['titulo', 'autor', 'isbn', 'editorial', 'año_publicacion'])

def datos_completos_usuario(usuario_data):
    return all(k in usuario_data and usuario_data[k] for k in ['id_usuario', 'nombre', 'email', 'contrasena', 'rol'])

if __name__ == '__main__':
    cargar_datos()
    host = '127.0.0.1'
    port = 5000
    print(f"Iniciando servidor Flask en http://{host}:{port} — abre esta URL en tu navegador")
    app.run(host=host, port=port, debug=True)