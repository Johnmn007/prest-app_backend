from datetime import timedelta

class ServicioPrestamo:
    @staticmethod
    def calcular_y_preparar_prestamo(datos_prestamo):
        # Lógica Financiera
        monto_total = datos_prestamo.monto_principal * (1 + datos_prestamo.tasa_interes)
        pago_diario = monto_total / datos_prestamo.total_cuotas
        
        # Generar cronograma de cuotas
        cuotas = []
        for i in range(1, datos_prestamo.total_cuotas + 1):
            nueva_cuota = {
                "numero_cuota": i,
                "fecha_vencimiento": datos_prestamo.fecha_inicio + timedelta(days=i),
                "monto_cuota": pago_diario,
                "estado": "PENDIENTE"
            }
            cuotas.append(nueva_cuota)
            
        return monto_total, pago_diario, cuotas