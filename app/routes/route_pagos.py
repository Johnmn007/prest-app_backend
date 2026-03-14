@ruta.post("/registrar")
def registrar_pago(pago: EsquemaPago, db: Session = Depends(obtener_db)):
    # 1. Buscar la cuota pendiente más antigua del préstamo
    # 2. Aplicar el monto del pago
    # 3. Si el pago cubre la cuota, marcar como PAGADO
    # 4. Si sobra dinero, aplicarlo a la siguiente cuota (Pago adelantado)
    # 5. Actualizar el estado del préstamo si todas las cuotas están pagadas
    pass