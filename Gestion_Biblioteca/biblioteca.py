class Libro:
    def __init__(self, titulo, autor, isbn, editorial, año_publicacion):
        self.titulo = titulo
        self.autor = autor
        self.isbn = isbn
        self.editorial = editorial
        self.año_publicacion = año_publicacion
        self.disponible = True

    def mostrar_info(self):
        return f"{self.titulo} por {self.autor}, ISBN: {self.isbn}"

    def actualizar_disponibilidad(self, disponible):
        self.disponible = disponible
        estado = "Disponible" if disponible else "No disponible"
        print(f"El libro {self.titulo} ahora está {estado}")


class Usuario:
    def __init__(self, id_usuario, nombre, email, contrasena, rol):
        self.id_usuario = id_usuario
        self.nombre = nombre
        self.email = email
        self.contrasena = contrasena
        self.rol = rol 
        self.libros_prestados = []

    def prestar_libro(self, libro): 
        if libro.disponible:
            self.libros_prestados.append(libro)
            libro.actualizar_disponibilidad(False) 
            print(f"El libro {libro.titulo} prestado a {self.nombre}.")
        else:
            print("Este libro no está disponible para préstamo")

    def devolver_libro(self, libro):
        if libro in self.libros_prestados:
            self.libros_prestados.remove(libro)
            libro.actualizar_disponibilidad(True)  
            print(f"Libro {libro.titulo} devuelto por {self.nombre}.") 


class Bibliotecario:
    def __init__(self, id_bibliotecario, nombre):
        self.id_bibliotecario = id_bibliotecario
        self.nombre = nombre

    def añadir_libro(self, biblioteca, libro):
        biblioteca.libros.append(libro)
        print(f"Libro {libro.titulo} añadido a la biblioteca")

    def eliminar_libro(self, biblioteca, libro):
        if libro in biblioteca.libros:
            biblioteca.libros.remove(libro)
            print(f"El libro {libro.titulo} fue eliminado de la biblioteca")
        else:
            print("Este libro no está registrado en la biblioteca")


class Biblioteca:
    def __init__(self):
        self.libros = []
        self.usuarios = []
        self.bibliotecarios = []
        self.prestamos = []

    def registrar_usuarios(self, usuario):
        self.usuarios.append(usuario)
        print(f"Usuario {usuario.nombre} registrado en el sistema.")

    def eliminar_usuario(self, usuario):  
        if usuario in self.usuarios:
            self.usuarios.remove(usuario)
            print(f"Usuario {usuario.nombre} fue eliminado del sistema.")

    def listar_libros(self):
        for libro in self.libros:
            print(libro.mostrar_info())

    def listar_usuarios(self):
        for usuario in self.usuarios:
            print(f"{usuario.nombre}, Email: {usuario.email}")  


class Prestamo:
    def __init__(self, id_prestamo, libro, usuario, fecha_prestamo, fecha_devolucion): 
        self.id_prestamo = id_prestamo
        self.libro = libro
        self.usuario = usuario
        self.fecha_prestamo = fecha_prestamo
        self.fecha_devolucion = fecha_devolucion

    def finalizar_prestamo(self):
        print(f"""El préstamo del libro {self.libro.titulo} ha finalizado.
Debe ser devuelto por {self.usuario.nombre} antes de {self.fecha_devolucion}.""")