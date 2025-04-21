import os
from flask import Flask, render_template, request, jsonify, send_file
from flask_pymongo import PyMongo
from datetime import datetime

# Configuración inicial
app = Flask(__name__)
app.config["MONGO_URI"] = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/avicola")
mongo = PyMongo(app)

# Página principal
@app.route("/")
def index():
    return render_template("index.html")

# Ruta para registrar huevos
@app.route("/registrar_huevos", methods=["GET", "POST"])
def registrar_huevos():
    if request.method == "POST":
        try:
            data = request.get_json()  # Obtener datos en formato JSON
            tipo = data.get("tipo")
            tamaño = data.get("tamaño")
            cantidad = data.get("cantidad")

            if not tipo or not tamaño or not cantidad:
                return jsonify({"mensaje": "Datos incompletos"}), 400

            # Actualizar el stock en MongoDB
            stock = mongo.db.stock
            stock.update_one(
                {"tipo": tipo, "tamaño": tamaño},
                {"$inc": {"cantidad": int(cantidad)}},
                upsert=True
            )
            return jsonify({"mensaje": "Huevos registrados exitosamente"})
        except Exception as e:
            return jsonify({"mensaje": "Error al registrar los huevos", "error": str(e)}), 500

    # Si es una solicitud GET, renderiza el formulario
    return render_template("registrar_huevos.html")

# Ruta para ver el stock
@app.route("/ver_stock")
def ver_stock():
    stock = mongo.db.stock.find()
    return render_template("ver_stock.html", stock=stock)

# Ruta para registrar clientes
@app.route("/registrar_cliente", methods=["GET", "POST"])
def registrar_cliente():
    if request.method == "POST":
        try:
            data = request.get_json()  # Obtener datos JSON
            nombre = data.get("nombre")
            tipo = data.get("tipo")  # Persona Natural o Jurídica
            identificacion = data.get("identificacion")

            if not nombre or not tipo or not identificacion:
                return jsonify({"mensaje": "Datos incompletos"}), 400

            # Insertar cliente en la base de datos
            clientes = mongo.db.clientes
            clientes.insert_one({
                "nombre": nombre,
                "tipo": tipo,
                "identificacion": identificacion
            })
            return jsonify({"mensaje": "Cliente registrado exitosamente"})
        except Exception as e:
            return jsonify({"mensaje": "Error al registrar cliente", "error": str(e)}), 500

    # Renderizar la página en caso de una solicitud GET
    return render_template("registrar_cliente.html")

# Prueba de conexión a la base de datos
@app.route("/prueba_conexion")
def prueba_conexion():
    try:
        db_names = mongo.db.list_collection_names()
        return f"Conectado a MongoDB. Colecciones disponibles: {db_names}"
    except Exception as e:
        return f"Error al conectar con MongoDB: {str(e)}"

# Ruta para realizar la compra de huevos

@app.route("/comprar", methods=["GET", "POST"])
def comprar_huevos():
    if request.method == "GET":
        # Renderizar el formulario HTML de compras
        return render_template("comprar_huevos.html")

    if request.method == "POST":
        try:
            print(f"Método recibido: {request.method}")
            print(f"Encabezado Content-Type: {request.headers.get('Content-Type')}")
            print(f"Datos en bruto: {request.data}")

            # Procesar datos JSON enviados en la solicitud POST
            data = request.get_json(force=True)
            print(f"Datos procesados como JSON: {data}")

            if not data:
                return jsonify({"mensaje": "No se enviaron datos en formato JSON."}), 400

            cliente_id = data.get("cliente")
            tipo = data.get("tipo")
            cantidad = int(data.get("cantidad"))  # Puede ser 12 o 30
            tamaño = data.get("tamaño")
            total = 0

            # Obtener precios por cubeta y por huevo individual
            precios_cubeta = {
                "Rojo": {"A": 12000, "AA": 13500, "B": 11000, "EXTRA": 15000},
                "Blanco": {"A": 10000, "AA": 11500, "B": 9500, "EXTRA": 14000}
            }
            precios_individual = {
                "Rojo": {"A": 400, "AA": 450, "B": 367, "EXTRA": 500},
                "Blanco": {"A": 333, "AA": 383, "B": 317, "EXTRA": 467}
            }

            # Validar datos básicos
            if not cliente_id or not tipo or not tamaño or not cantidad:
                return jsonify({"mensaje": "Datos incompletos."}), 400

            # Verificar existencia del cliente
            cliente = mongo.db.clientes.find_one({"identificacion": cliente_id})
            if not cliente:
                return jsonify({"mensaje": "Cliente no encontrado en la base de datos."}), 404

            # Validar reglas según el tipo de cliente
            if cliente["tipo"] == "Natural" and cantidad not in [12, 30]:
                print("Regla violada: Natural sólo docenas o cubetas.")
                return jsonify({"mensaje": "Una persona natural puede comprar únicamente por docena (12) o por cubeta (30)."}), 400

            if cliente["tipo"] == "Juridica" and cantidad != 30:
                print("Regla violada: Jurídica solo cubetas.")
                return jsonify({"mensaje": "Una persona jurídica solo puede comprar cubetas (30 huevos)."}), 400

            # Calcular el precio total basado en la cantidad
            if cantidad == 12:  # Si es una docena, cobramos por huevo individual
                precio_huevo = precios_individual[tipo][tamaño]  # Precio por huevo individual
                total = precio_huevo * cantidad
            elif cantidad == 30:  # Si es una cubeta, cobramos por cubeta
                total = precios_cubeta[tipo][tamaño]  # Precio por cubeta
            else:
                return jsonify({"mensaje": "Cantidad no válida. Solo puede comprar por docena (12) o cubeta (30)."}), 400
 
 # Calcular el IVA y el total con IVA
            iva = total * 0.05
            total_con_iva = total + iva
# Crear la factura en formato txt
            factura_contenido = f"""
               ,~.
             ,-'__ `-,
            (()),-' `. `.                ,'))
           ,( o )   `-.__         ,',')~.
          <=.) (         `-.__,==' ' ')
            (   )                      )
             `-'\   ,                  )
                 |  \\        `~.      /
                 \\   `._        \\    /
                  \\     `._____,'   /
                   `-.           ,'
                      `-._   _,-'
                          `""`

                                        .-.
                                       /   \\
                                      |     |
                                       \\___/
                                           

        Granja Feliz
      NIT: 870545489-0
      Factura de Venta
----------------------------------------
Nombre del Cliente: {cliente["nombre"]}
NIT o CC del Cliente: {cliente["identificacion"]}
----------------------------------------
Artículo(s):
{cantidad} {tipo} tamaño {tamaño}
----------------------------------------
Valor Total (sin IVA): ${total:.2f}
IVA (5%): ${iva:.2f}
Valor Total (con IVA): ${total_con_iva:.2f}
----------------------------------------
"""
            nombre_archivo = f"factura_{cliente['identificacion']}.txt"
            with open(nombre_archivo, "w", encoding="utf-8") as factura:
                factura.write(factura_contenido)
            print(f"Factura generada: {nombre_archivo}")

            # Verificar existencia y disponibilidad en el stock
            stock = mongo.db.stock.find_one({"tipo": tipo, "tamaño": tamaño})
            if not stock or stock.get("cantidad", 0) < cantidad:
                return jsonify({"mensaje": f"Stock insuficiente para {tipo} tamaño {tamaño}. Disponible: {stock.get('cantidad', 0)}"}), 400

            # Actualizar el stock
            mongo.db.stock.update_one(
                {"tipo": tipo, "tamaño": tamaño},
                {"$inc": {"cantidad": -cantidad}}
            )
            print("Stock actualizado correctamente.")

            # Registrar la compra
            mongo.db.compras.insert_one({
                "cliente_id": cliente_id,
                "tipo": tipo,
                "tamaño": tamaño,
                "cantidad": cantidad,
                "total": total,
                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Fecha y hora actual
            })
            print("Compra registrada correctamente en MongoDB.")

            # Generar respuesta de éxito
            return jsonify({
                "mensaje": "Compra realizada correctamente.",
                "cliente": cliente["nombre"],
                "tipo": tipo,
                "tamaño": tamaño,
                "cantidad": cantidad,
                "total": total,
                "iva": iva,
                "total_con_iva": total_con_iva,
                "factura": nombre_archivo
            })
        except Exception as e:
            print(f"Excepción inesperada: {str(e)}")
            return jsonify({"mensaje": "Error procesando la compra.", "error": str(e)}), 500


    


        
# Ruta para obtener clientes
@app.route("/obtener_clientes", methods=["GET"])
def obtener_clientes():
    try:
        clientes = mongo.db.clientes.find()
        lista_clientes = [{"nombre": cliente["nombre"], "identificacion": cliente["identificacion"]} for cliente in clientes]
        return jsonify(lista_clientes)
    except Exception as e:
        return jsonify({"mensaje": "Error al obtener clientes", "error": str(e)}), 500

@app.route("/historial_compras", methods=["GET"])
def historial_compras():
    try:
        # Obtener todos los clientes desde la colección "clientes"
        clientes = list(mongo.db.clientes.find())
        
        # Obtener todas las compras desde la colección "compras"
        compras = list(mongo.db.compras.find())

        # Crear un historial organizado por cliente
        historial = []
        for cliente in clientes:
            cliente_compras = [
                compra for compra in compras if compra["cliente_id"] == cliente["identificacion"]
            ]
            historial.append({
                "nombre": cliente["nombre"],
                "identificacion": cliente["identificacion"],
                "compras": cliente_compras
            })

        return render_template("historial_compras.html", historial=historial)

    except Exception as e:
        print(f"Error al cargar el historial de compras: {str(e)}")
        return f"Error al cargar el historial de compras: {str(e)}", 500

@app.route("/descargar_factura", methods=["GET"])
def descargar_factura():
    try:
        archivo = request.args.get("archivo")
        if not archivo:
            return "Archivo no especificado.", 400
        
        # Path del archivo
        path_archivo = os.path.join(os.getcwd(), archivo)
        
        if not os.path.exists(path_archivo):
            return "Archivo no encontrado.", 404
        
        # Enviar el archivo al cliente
        return send_file(path_archivo, as_attachment=True)
    except Exception as e:
        print(f"Error al descargar factura: {str(e)}")
        return f"Error al descargar factura: {str(e)}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))