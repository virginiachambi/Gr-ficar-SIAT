from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import pandas as pd
import os
from werkzeug.utils import secure_filename
import matplotlib.pyplot as plt
import io
import seaborn as sns

def crear_app():
    app = Flask(__name__)
    app.secret_key = 'supersecretkey'

    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'xlsx'}
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    @app.route("/", methods=["GET", "POST"])
    def index():
        head_data = None  # Variable para almacenar el head de los datos

        if request.method == "POST":
            file = request.files.get("file")

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)

                try:
                    data = pd.read_excel(file_path)
                    head_data = data.head()  # Obtener los primeros 5 registros
                except ValueError as e:
                    flash(f"Error al leer el archivo de Excel: {str(e)}", "danger")
                    return redirect(url_for('index'))
                except Exception as e:
                    flash(f"Ocurrió un error inesperado: {str(e)}", "danger")
                    return redirect(url_for('index'))
            else:
                flash("Por favor, suba un archivo con extensión .xlsx", "warning")
                return redirect(url_for('index'))

        return render_template("index.html", head_data=head_data)

    @app.route("/plot.png")
    def plot_png():
        latest_file = max([os.path.join(app.config['UPLOAD_FOLDER'], f) for f in os.listdir(app.config['UPLOAD_FOLDER'])], key=os.path.getctime)
        data = pd.read_excel(latest_file)

        # Agrupar por fecha y sumar los importes
        data['FECHA DE LA FACTURA'] = pd.to_datetime(data['FECHA DE LA FACTURA'])
        grouped_data = data.groupby('FECHA DE LA FACTURA')['IMPORTE TOTAL DE LA VENTA'].sum().reset_index()

        # Crear la gráfica
        sns.set(style="whitegrid")
        plt.figure(figsize=(10, 6))
        ax = sns.lineplot(x=grouped_data['FECHA DE LA FACTURA'], y=grouped_data['IMPORTE TOTAL DE LA VENTA'], marker="o", color='dodgerblue')

        ax.set_xlabel('Fecha', fontsize=12)
        ax.set_ylabel('Importe Total de la Venta', fontsize=12)
        ax.set_title('Importe Total de la Venta por Día', fontsize=14)
        plt.xticks(rotation=45)  # Rotar las fechas para mejor visibilidad

        # Guardar el gráfico en un objeto de bytes
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight')
        img.seek(0)
        plt.close()

        return send_file(img, mimetype='image/png')

    return app

app = crear_app()

if __name__ == "__main__":
    app.run(debug=True)
