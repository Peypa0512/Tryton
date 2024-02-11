from datetime import datetime

from trytond.model import ModelSQL, ModelView, fields, Unique
#from trytond.modules.company import CompanyReport
import trytond.pyson
from trytond.pool import Pool, PoolMeta
from trytond.report import Report
from trytond.transaction import Transaction
from trytond.wizard import Wizard, StateView, StateTransition, Button


class Marca(ModelSQL, ModelView):
    'Marca'
    __name__ = 'taller.marca'
    name = fields.Char('Nombre', required=True)
    modelos = fields.One2Many('taller.modelo', 'marca', 'Modelos')


class Modelo(ModelSQL, ModelView):
    'Modelo'
    __name__ = "taller.modelo"
    _rec_name = 'modelo' # para que imprima el nombre del modelo y no el id
    marca = fields.Many2One('taller.marca','Marca', required=True, ondelete='CASCADE')
    modelo = fields.Char('modelo', required=True)
    precio_mod = fields.Integer('PVP')
    fecha_lanz = fields.Date('Fecha Lanzamiento')
    # prod_modelo = fields.Many2One('product.template', 'Producto Disponible', ondelete='CASCADE')
    prod_modelo = fields.Many2Many('modelo-producto', 'modelo', 'producto', 'Producto Disponible',
        domain=[
            ('type', '=', 'goods')
        ])
    combustible = fields.Selection([
        ('g','Gasolina'),
        ('d', 'Diesel'),
        ('e', 'Electrico'),
        ('h', 'Hibrido'),
        (None, "")], 'Tipo de combustible') #none si no queremos elegir tipo de combustible
    caballos = fields.Integer('Numeros de caballos')

       #hacemos la función de valor por defecto

    @classmethod
    def default_fecha_lanz(cls):
        return datetime.today()

    # hacemos que nos de por defecto el id del primer valor de la tabla Marca

    @classmethod
    def default_marca(cls):
        pool = Pool()
        if pool != None:
                Marca = pool.get('taller.marca')
                marca_1 = Marca.search([], limit=1, order=[
                          ('id', 'ASC'),
                          ('name', 'ASC')])
                return marca_1[0].id

        return 0


class Coche(ModelSQL, ModelView):
    'Coche'
    __name__ = 'taller.coche'
    _rec_name = 'modelo'
    matricula = fields.Char('Matricula', required=True,
                            states= {
                                'readonly': trytond.pyson.Greater(trytond.pyson.Eval('id', -1), 0)
                            })
    propietario = fields.Many2One('party.party', 'Propietario', required=True, ondelete='CASCADE')
    marca = fields.Many2One('taller.marca', 'Marca', ondelete='CASCADE')
    modelo = fields.Many2One('taller.modelo', 'Modelo', ondelete='CASCADE',
                             domain=[
                                 ('marca', '=', trytond.pyson.Eval('marca', -1))
                             ],
                             depends=['marca'], # para indicar que modelo depende de la marca
                             states={
                                 'required': trytond.pyson.Bool(trytond.pyson.Eval('marca', -1)),
                                 'invisible': ~trytond.pyson.Bool(trytond.pyson.Eval('marca', -1))
                             }

                             ) # creamos un dominio para filtrar
    precio = fields.Integer('precio',
                            domain=['OR',
                            ('precio', '>', 0),
                            ('precio', '=', None)
                            ])
    fecha_matriculacion = fields.Date('Fecha matriculacion')
    fecha_baja = fields.Date('Fecha baja')
    fecha_imp = fields.Function(fields.Date('Fecha Lanzamiento'), 'getFecha_Lanz', searcher='searcher_fech_lanz')

    caballos = fields.Function(fields.Integer('caballos'), 'get_caballos', searcher='searcher_caballos')


    @classmethod
    def __setup__(cls):
        super().__setup__()
        t = cls.__table__()
        cls._sql_constraints = [
             ('matriculate_uniq', Unique(t, t.matricula), 'taller.msg_coche_matricula_unique')
         ]

    @fields.depends('marca', 'modelo')
    def on_change_marca(self):
        # poner precio por defecto en marca nueva
        if self.marca:
            if len(self.marca.modelos) == 1:
                self.modelo = self.marca.modelos[0]
                print(self.modelo.modelo)
            # asignamos un valor a otro atributo
            # cuando cambiamos la marca cambiamos el modelo
            # cambiar de marca de coche
            if self.modelo and self.modelo.marca.id != self.marca.id:
                self.modelo = None
                print('funciona')
        else:
            return None

    @fields.depends('marca', 'modelo')
    def on_change_with_precio(self):
        if self.marca and self.modelo:
            print(self.modelo.precio_mod)
            return self.modelo.precio_mod

    def get_caballos(self,name):
        if self.modelo:
            return self.modelo.caballos
        else:
            return 0
    def getFecha_Lanz(self, name):
        # si quiero poder una fecha concreta
        if self.modelo and self.modelo.fecha_lanz:
            #return datetime(2022, 3, 3) # introducimos una fecha fija
            return self.modelo.fecha_lanz
        else:
            return datetime(1111, 11, 11)

    # metemos el searcher detras del getter
    @classmethod
    def searcher_caballos(cls, name, clause):
        print(name, clause)
        return [
            ('modelo.caballos', clause[1], clause[2])

    # nos mostrara la fecha de lanzamiento
                           ]
    @classmethod
    def searcher_fech_lanz(cls, name, clause):
        print(name, clause)
        return [
            ('modelo.fecha_lanz', '=', clause)
    ]
 # cuando modificamos una clase ya existente no ponemos model sino metaclass
class Party(metaclass=PoolMeta):
     __name__= 'party.party'
     # mostrar los coches de un tercero
     coche = fields.One2Many('taller.coche', 'propietario', 'coches')  # propietario es el campo al que hace referencia

     #modificamos el campo existe name
     @classmethod
     def __setup__(cls):
        super().__setup__()
        # ponemos el requeried del campo name a true
        cls.name.required=True
        # para que no podamos modificar el nombre si tenemos ya guardado el id
        cls.name.states.update({
             'readonly': trytond.pyson.Eval('id', -1) > 0
         })


class Productos(metaclass=PoolMeta):
        __name__ = 'product.template'
        #modelo_compatible = fields.One2Many('taller.modelo', 'prod_modelo', 'Modelos Compatibles')
        modelo_compatible = fields.Many2Many('modelo-producto', 'producto', 'modelo',  'Modelo Compatible',
        states={
           'invisible': trytond.pyson.Bool(trytond.pyson.Eval('type', '') != 'goods')
        },
        depends=['type'],
        )

class Modelo_Producto(ModelSQL):

    'Modelo-Producto'
    __name__ = 'modelo-producto'

    modelo = fields.Many2One('taller.modelo', 'modelo', required=True, ondelete='CASCADE')
    producto = fields.Many2One('product.template', 'producto', required=True, ondelete='CASCADE')

 # #hay que crear una clase para la fecha de baja del coche


# hay que crear una clase que nos muestre los coches que se han dado de baja
class Baja_coche_resultado(ModelView):
    'Baja Coche'
    __name__ = 'taller.baja_coche.result'
    # ahora los campos que quiere que vea el usuario
    baja_coches = fields.Integer('Coches dados de baja', readonly=True)

    # nos va a dar el numero de coches dados de baja
    @classmethod
    def default_baja_coche(cls):
        return len(Transaction().context['active_ids'])




# asistente para dar de baja a coches
class Dar_baja_coches(Wizard):
    'Baja Coche'
    __name__ = 'taller.baja_coche'
    start = StateView('taller.baja_coche.start', 'taller.baja_coche_start_form', [
        Button('Cancelar', 'end', 'tryton-cancel'),
        Button('Baja', 'baja', 'tryton-ok', default=True),
        ])
    baja = StateTransition()
    result = StateView('taller.baja_coche.result', "taller.baja_coche_resultado_form", [
        Button('Cerrar', 'end', 'tryton-close')
    ])
    def transition_baja(self):
        # tenemos que hacer una instancia pool y coger la clase coche
        pool = Pool()
        Coche = pool.get('taller.coche')

        #para cargar las instancias de los coches seleccionados
        coches = Coche.browse(Transaction().context['active_ids'])


        #ahora hay que escribir la fecha de baja
        for coche in coches:
            coche.fecha_baja = self.start.fecha_baja


        # hay que persistir esto en memoria por que utilizaremos 'save',
        # se suelen guardar todos los registros de golpe
        Coche.save(coches)

        #una vez hecha la baja hay que poner el resultado
        #self.result.default_coche_afectado
        return "result"



class Baja_coche_start(ModelView):
    'Fecha Baja Coche'
    __name__ = 'taller.baja_coche.start'
    #ahora los campos que quiere que vea el usuario
    fecha_baja = fields.Date('Fecha baja', required=True)

    # fecha baja por defecto
    @classmethod
    def default_fecha_baja(cls):
        return datetime.today()


class Empresa(Report):
        'Empresa'
        __name__ = 'ficha_tecnica_del_coche'

        @classmethod
        def get_context(cls, records, header, data):
            context = super().get_context(records, header, data)
            context['empresa'] = 'Peypa'
            return context


# class Empresa2(CompanyReport): #-> para compania en bbdd
#     'Empresa'
#     __name__ = 'ficha_tecnica_del_coche'
#
#     @classmethod
#     def get_context(cls, records, header, data):
#         context = super().get_context(records, header, data)
#         context['empresa'] = 'Peypa'
#         return context