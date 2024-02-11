from trytond.pool import Pool
from . import taller

__all__ = ['register']




def register():
    Pool.register(
        taller.Marca,
        taller.Modelo,
        taller.Coche,
        taller.Productos,
        taller.Modelo_Producto,
        taller.Baja_coche_start,
        taller.Baja_coche_resultado,
        module='taller', type_='model')
    Pool.register(
        taller.Dar_baja_coches,
        module='taller', type_='wizard')
    Pool.register(
        taller.Empresa,
        module='taller', type_='report')
