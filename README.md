# Predictive Container Migration (PCM V5)

## 1. Descripción del proyecto

**Predictive Container Migration (PCM V5)** es un prototipo experimental de gestión de contenedores Docker que utiliza técnicas de aprendizaje profundo para analizar el consumo de CPU y apoyar decisiones de conmutación de tráfico entre nodos.

El proyecto implementa y evalúa dos estrategias:

- **Controlador predictivo:** utiliza un modelo LSTM (Long Short-Term Memory) entrenado para estimar el comportamiento futuro del consumo de CPU.
- **Controlador reactivo:** utiliza mediciones actuales de CPU y reglas basadas en umbrales para decidir cuándo realizar una conmutación.

El sistema se desarrolla sobre tres máquinas virtuales Ubuntu, utilizando Docker, Flask, Nginx, Python y TensorFlow.

**Alcance:** PCM V5 implementa conmutación de tráfico entre réplicas de una aplicación desplegadas previamente en distintos nodos. No realiza migración en vivo del estado de ejecución de un contenedor.

## 2. Objetivo general

Diseñar e implementar un sistema experimental de gestión de contenedores que utilice predicciones LSTM y métricas de recursos para evaluar decisiones de conmutación entre nodos, comparando una estrategia predictiva con otra reactiva.

### Objetivos específicos

1. Implementar una infraestructura virtualizada con tres nodos interconectados.
2. Desplegar aplicaciones Flask mediante contenedores Docker.
3. Recopilar métricas de utilización de CPU y memoria RAM.
4. Entrenar y evaluar un modelo LSTM para predicción de CPU.
5. Implementar controladores predictivo y reactivo.
6. Configurar Nginx como proxy inverso para dirigir el tráfico.
7. Evaluar el comportamiento del sistema mediante escenarios de carga Growth y Spike.
8. Comparar las predicciones del LSTM con un baseline de persistencia.

## 3. Arquitectura del sistema

El entorno experimental utiliza tres máquinas virtuales en VirtualBox.

| Nodo | Dirección IP de laboratorio | Función |
|---|---|---|
| PCM-Node1 | 192.168.56.11 | Aplicación Flask principal y entorno LSTM |
| PCM-Node2 | 192.168.56.12 | Orquestador, controladores y proxy Nginx |
| PCM-Node3 | 192.168.56.13 | Réplica Flask de destino |

### Flujo de funcionamiento

1. Los clientes acceden al servicio a través del proxy Nginx de Node2.
2. Nginx dirige inicialmente el tráfico hacia la aplicación principal de Node1.
3. El sistema recopila métricas de utilización de CPU.
4. El controlador predictivo o reactivo evalúa las condiciones del sistema.
5. Cuando se cumplen las condiciones configuradas y se autoriza la operación, el orquestador puede cambiar el destino del tráfico hacia Node3.
6. Se comprueba el resultado de la conmutación y se registran las métricas correspondientes.

La conmutación se realiza entre aplicaciones previamente desplegadas. No implica transferir automáticamente memoria, procesos ni estado interno del contenedor.

## 4. Tecnologías utilizadas

| Tecnología | Utilización |
|---|---|
| VirtualBox | Virtualización de la infraestructura |
| Ubuntu Server 20.04 LTS | Sistema operativo de los nodos del laboratorio |
| Docker | Ejecución de contenedores |
| Python | Desarrollo de controladores y scripts |
| Flask | Aplicación web de prueba |
| TensorFlow / Keras | Entrenamiento e inferencia del modelo LSTM |
| NumPy | Procesamiento numérico y normalización |
| Nginx | Proxy inverso y conmutación de tráfico |
| SSH / SCP | Comunicación y transferencia de archivos entre nodos |
| CSV / JSON | Almacenamiento de métricas y resultados |

## 5. Estructura del repositorio

```text
PCM-V5-GitHub/
├── README.md
├── node1/
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── modelo_lstm_v5/
│   │   ├── cpu_forecaster_pcm_v5.keras
│   │   ├── parametros_normalizacion_pcm_v5.npz
│   │   ├── metricas_v5.json
│   │   └── predicciones_vs_reales_v5.csv
│   ├── scripts_lstm_v5/
│   │   ├── entrenar_v5.py
│   │   ├── exportar_predicciones_v5.py
│   │   └── predecir.py
│   └── evaluacion_lstm_v5/
│       ├── growth_v5_20261110_020233.csv
│       ├── spike_v5_20261110_020639.csv
│       └── predicciones_nuevas_v5.csv
├── node2/
│   ├── scripts/
│   ├── config/
│   ├── datos_evaluacion/
│   ├── experimentos_v5_nuevos/
│   ├── resultados/
│   ├── graficas/
│   ├── comparacion_v5/
│   └── metricas/
├── node3/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
└── documentacion/
```

La estructura puede ampliarse con configuraciones de despliegue y documentación adicional.

## 6. Aplicación Flask y contenedores Docker

El sistema utiliza una aplicación Flask que permite generar cargas de procesamiento y observar el comportamiento de CPU.

### Node1 — Aplicación principal

- Contenedor: `pcm-flask-app`
- Puerto de aplicación: `5000`

### Node3 — Réplica de destino

- Contenedor de prueba: `pcm-flask-migracion-test`
- Puerto de aplicación: `5001`

Los archivos `Dockerfile`, `app.py` y `requirements.txt` de cada nodo permiten consultar la implementación de las aplicaciones.

El despliegue debe realizarse de acuerdo con la configuración de puertos y redes del entorno.

## 7. Modelo predictivo LSTM V5

El sistema utiliza un modelo LSTM para estimar el porcentaje de utilización de CPU a partir de una secuencia de observaciones anteriores.

### Modelo entrenado

Archivo:

`node1/modelo_lstm_v5/cpu_forecaster_pcm_v5.keras`

### Parámetros de normalización

Archivo:

`node1/modelo_lstm_v5/parametros_normalizacion_pcm_v5.npz`

Los parámetros permiten aplicar la transformación utilizada para preparar los valores de CPU que recibe el modelo.

### Ventana temporal

El script de evaluación utiliza una ventana de **10 observaciones consecutivas** de CPU para generar cada predicción.

### Scripts

- `entrenar_v5.py`: entrenamiento y generación de archivos del modelo.
- `exportar_predicciones_v5.py`: exportación de predicciones.
- `predecir.py`: evaluación sobre escenarios Growth y Spike.

Las rutas de archivos y dependencias deben verificarse antes de ejecutar estos scripts en un entorno diferente.

## 8. Controlador predictivo

El controlador predictivo se encuentra en:

`node2/scripts/controlador_pcm_v5.py`

Este componente utiliza información de CPU y predicciones del modelo LSTM para evaluar las condiciones de conmutación.

La ejecución de una conmutación depende de las condiciones implementadas en el controlador y de su autorización correspondiente.

Una predicción elevada no implica necesariamente que se produzca una conmutación: deben cumplirse las reglas establecidas.

## 9. Controlador reactivo

El controlador reactivo se encuentra en:

`node2/scripts/controlador_pcm_reactivo_v5.py`

Este componente utiliza mediciones recientes de CPU y criterios basados en umbrales.

En las pruebas del proyecto se utilizó una ventana de 10 mediciones, con un criterio de al menos 7 observaciones superiores al 80 % de utilización de CPU, junto con verificaciones adicionales del nodo de destino.

El controlador permite estudiar una estrategia basada en condiciones observadas, sin depender de predicciones LSTM.

## 10. Conmutación de tráfico mediante Nginx

Nginx funciona como proxy inverso en PCM-Node2 y permite dirigir las solicitudes hacia la aplicación activa.

El script:

`node2/scripts/cambiar_trafico.py`

participa en el cambio del destino del tráfico.

El proxy utiliza el puerto `8081` en el entorno experimental.

**Importante:** las configuraciones efectivas de Nginx, las rutas SSH y los permisos deben adaptarse al entorno de ejecución. El repositorio no debe incluir claves privadas ni contraseñas.

## 11. Escenarios experimentales

### Growth — Crecimiento de carga

Este escenario genera un comportamiento de carga creciente para observar la evolución de la utilización de CPU y analizar las respuestas de los controladores.

### Spike — Picos de carga

Este escenario genera incrementos pronunciados de utilización de CPU para evaluar la reacción del sistema ante situaciones de carga elevada.

### Evaluación

Se recopilan métricas como:

- Porcentaje de utilización de CPU.
- Consumo de memoria RAM.
- Predicción de utilización de CPU.
- Estado de conmutación.
- Tiempo de conmutación.
- Resultados de disponibilidad y evaluación.

Los datasets y registros experimentales se encuentran en las carpetas de evaluación y experimentos del repositorio.

## 12. Resultados experimentales

Durante pruebas individuales del prototipo se observaron conmutaciones exitosas mediante ambas estrategias.

| Indicador | Controlador predictivo | Controlador reactivo |
|---|---|---|
| Tipo de decisión | Predicción LSTM y reglas | Mediciones actuales y umbrales |
| Ejemplo de medición | CPU predicha: 82.995 % | CPU media: 83.014 % |
| Ejemplo de tiempo de conmutación | 1.2154 s | 1.3117 s |

Estos valores corresponden a ejecuciones específicas y no representan promedios estadísticos ni demuestran superioridad general de una estrategia.

### Comparación del LSTM con baseline de persistencia

En una evaluación de 102 registros emparejados se obtuvieron los siguientes resultados:

| Métrica | LSTM V5 | Baseline de persistencia |
|---|---:|---:|
| MAE | 10.6376 | 3.1481 |
| RMSE | 15.0126 | 9.7821 |

Los errores están expresados en puntos porcentuales de CPU.

En esta evaluación, el baseline de persistencia presentó menor error que el modelo LSTM.

Esto indica que el modelo predictivo requiere evaluación y posibles mejoras adicionales antes de afirmar que supera a un método de referencia simple.

## 13. Instalación y requisitos

Para reproducir el entorno se requiere:

- Tres máquinas virtuales Ubuntu con conectividad de red.
- Docker en los nodos de aplicación.
- Python y las dependencias utilizadas por los scripts.
- TensorFlow/Keras y NumPy para la inferencia LSTM.
- Nginx en el nodo orquestador.
- Acceso SSH configurado entre los nodos correspondientes.
- Direcciones IP, rutas y permisos ajustados al entorno de laboratorio.

### Consideraciones de configuración

El archivo `node2/config/migracion.json` contiene parámetros específicos del entorno experimental, como direcciones IP, puertos, nombres de contenedores y rutas de claves SSH.

Las rutas de claves SSH son referencias locales. Las claves privadas deben generarse y almacenarse de manera segura fuera del repositorio.

Los scripts pueden requerir ajustes de rutas absolutas y dependencias antes de ejecutarse en otro equipo.

## 14. Ejecución y evaluación

La ejecución debe realizarse de forma controlada:

1. Iniciar las máquinas virtuales.
2. Verificar conectividad de red entre los nodos.
3. Confirmar que Docker y las aplicaciones Flask estén operativos.
4. Comprobar el funcionamiento del proxy Nginx.
5. Verificar el acceso al modelo LSTM y sus archivos auxiliares.
6. Ejecutar los scripts de recopilación y evaluación de métricas.
7. Generar escenarios Growth o Spike.
8. Ejecutar el controlador correspondiente siguiendo las condiciones y autorizaciones implementadas.
9. Consultar los registros, CSV y gráficas generados.

No se recomienda ejecutar scripts de conmutación sin revisar previamente sus parámetros y efectos.

## 15. Limitaciones

- El prototipo utiliza una infraestructura de laboratorio con tres máquinas virtuales.
- La conmutación de tráfico no equivale a migración en vivo del contenedor.
- Los resultados dependen de la carga generada, los recursos disponibles y la configuración de red.
- El modelo LSTM no superó al baseline de persistencia en la evaluación indicada.
- Los tiempos registrados corresponden a pruebas concretas y requieren más repeticiones para una comparación estadística.
- La reproducción completa exige configurar correctamente SSH, Docker, Nginx, dependencias y rutas de archivos.

## 16. Posibles mejoras

- Evaluar el LSTM con más escenarios y datos independientes.
- Optimizar el entrenamiento y la selección de características.
- Incorporar más métricas de recursos.
- Automatizar el despliegue de los nodos y contenedores.
- Centralizar la observabilidad y los registros.
- Realizar pruebas repetidas con análisis estadístico.
- Mejorar la portabilidad de las configuraciones y los scripts.
- Investigar mecanismos de migración real de contenedores con transferencia de estado.

## 17. Conclusiones

El proyecto PCM V5 demuestra la integración de virtualización, contenedores Docker, monitoreo de recursos, aprendizaje profundo y conmutación de tráfico en una infraestructura experimental.

La implementación de controladores predictivo y reactivo permite estudiar diferentes criterios para tomar decisiones operativas sobre la distribución del tráfico.

Los experimentos muestran que es posible realizar conmutaciones entre réplicas previamente desplegadas. Sin embargo, los resultados de predicción también evidencian la importancia de comparar modelos complejos con métodos de referencia sencillos y de evaluar su rendimiento con suficientes pruebas.

El repositorio reúne el código y los resultados experimentales del prototipo para facilitar su revisión académica y continuar mejorando su reproducibilidad.
