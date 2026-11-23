# CHULLS Seguros — base de conocimiento académica DEMO
Esta documentación es inventada únicamente para el proyecto académico. No constituye póliza real.

## SOAT
En el prototipo se ofrece SOAT de auto particular y motocicleta. El precio proviene únicamente de la tabla local precios_demo.json. Para avanzar se solicita tipo de vehículo, placa y teléfono de contacto. La emisión, el enlace de pago y el cobro son simulados; un asesor valida las condiciones.

## Qué es el SOAT
El SOAT (Seguro Obligatorio de Accidentes de Tránsito) es obligatorio en Perú para circular. Cubre a las personas (ocupantes y peatones) afectadas en un accidente de tránsito: gastos médicos, incapacidad, sepelio y muerte, según los montos que fija la norma. No cubre daños materiales al vehículo; para eso existe el seguro vehicular.

## Vehicular
El prototipo compara tres planes referenciales: Básico, Intermedio y Premium. Los precios mensuales referenciales están en precios_demo.json. Coberturas, deducibles, exclusiones, límites y servicios requieren confirmación contractual. No asegurar que el robo de espejos esté cubierto sin validar el condicionado y el plan contratado. Se registran vehículo, placa, teléfono y plan de interés para derivación.

## Deducible
El deducible es el monto o porcentaje del daño que asume el asegurado en cada siniestro antes de que la aseguradora pague. Planes con prima más baja suelen tener deducibles más altos. Los deducibles exactos de cada plan deben validarse con un asesor.

## Certificado y vigencia
El chatbot puede consultar la vigencia y el certificado de las pólizas registradas (archivo polizas.csv). Para ello pide la placa (ej. ABC-123) o el DNI del titular. Si no encuentra la póliza, deriva a un asesor. No afirmar la vigencia sin haber consultado el registro.

## Accidente
Primero comprobar si hay personas heridas y si la zona es segura. En caso de heridos o peligro inmediato, solicitar apoyo a los servicios de emergencia locales y escalar a una persona. No ofrecer asesoramiento médico ni legal. No admitir culpa ni prometer coberturas. Para accidentes sin heridos, orientar a tomar fotos, registrar placa del otro vehículo, datos de contacto y avisar a la aseguradora.

## Grúa
El chatbot no despacha grúas ni dispone de una central operativa real. Recaba ubicación general, placa, teléfono y descripción del incidente y deriva a una persona o canal oficial. No prometer tiempo de llegada ni cobertura.

## Estado de siniestro
Sin integración con el sistema de siniestros no es posible conocer estados reales. Pedir número de siniestro y teléfono de contacto y escalar a seguimiento humano.

## Renovación
Con la placa o el DNI, el chatbot revisa qué pólizas están vencidas o por vencer (30 días o menos) y si tienen renovación automática. Se recomienda renovar el SOAT antes de su vencimiento: no se puede circular con SOAT vencido. El prototipo no ejecuta pagos; la renovación la confirma un asesor.

## Asesor humano
Cuando el cliente lo pide, cuando hay heridos o cuando el caso requiere validar una póliza, el bot deriva a un asesor humano. Para ello registra placa y teléfono en una solicitud de derivación (simulada en esta demo).

## Restricciones
No emitir pólizas, cobrar, aprobar siniestros, garantizar indemnizaciones, dar asesoría legal o médica ni opinar sobre competidores. Nunca afirmar que los precios de la demostración son reales. Los casos urgentes con heridos deben escalar de inmediato.
