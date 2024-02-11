from proteus import config, Model, Wizard, Report
import csv

# para crear dentro de la tabla
config = config.set_trytond('cars_db')
Marca = Model.get('taller.marca')
Modelo = Model.get('taller.modelo')
lista_marca = {}
with open('cars_make.csv', newline="") as ficherocsv:
    fichero_lectura = csv.reader(ficherocsv, delimiter=",", quotechar="'")
    next(fichero_lectura)  # recorre la cabecera del fichero que no queremos
    for row in fichero_lectura:
        busqueda = Marca.find([('name', '=', row[1])])
        if not busqueda:
            newMarca = Marca()
            newMarca.name = row[1]
            newMarca.save()
            lista_marca[row[0]] = newMarca
            print("marca: ", lista_marca[row[0]].name, ": Guardada")
        else:
            lista_marca[row[0]] = busqueda[0]
            print("marca: ", busqueda[0].name, ":  Ya Guardada")

    # Marca.save(lista_marca)
    with open('car_model.csv', newline="") as ficherocsv:
        fichero_lectura2 = csv.reader(ficherocsv, delimiter=",", quotechar="'")
        next(fichero_lectura2)  # recorre la cabecera del fichero que no queremos
        lista_marca2 = []
        for row in fichero_lectura2:
            newModelo = Modelo()
            newModelo.marca = lista_marca[row[1]]
            newModelo.modelo = row[2]
            lista_marca2.append(newModelo)
        Modelo.save(lista_marca2)





           