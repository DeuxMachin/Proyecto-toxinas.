# Despliegue con Nginx Proxy Manager (NPM)

Este documento explica cómo exponer el contenedor de la API (Flask + Gunicorn) a través de Nginx Proxy Manager usando un puerto local en el VPS.

## 1) Ejecutar el contenedor en el VPS

El `docker-compose.yml` publica el servicio en el host (todas las interfaces):

- Servicio: `app`
- Puerto interno del contenedor: `5001`
- Puerto publicado en el host: `8087`

Iniciar en segundo plano:

```powershell
# En el VPS dentro del directorio del proyecto
docker compose up -d app
```

Verificar salud de la API desde el VPS:

```powershell
curl http://51.79.49.242:8087/v2/health
```

Debe responder con código 200.

## 2) Configurar Nginx Proxy Manager

1. Ingresar al panel de NPM
2. Ir a "Proxy Hosts" > "Add Proxy Host"
3. Campos básicos:
   - Domain Names: `tesis.brosdev.duckdns.org`
   - Scheme: `http`
   - Forward Hostname / IP: `51.79.49.242`
   - Forward Port: `8087`
   - Websockets Support: habilitado (si tu app los usa)
4. Pestaña SSL:
   - SSL Certificate: "Request a new SSL Certificate"
   - Force SSL: habilitado
   - HTTP/2 Support: habilitado
5. Guardar

Tras propagar el certificado, la app quedará accesible en:

- `https://tesis.brosdev.duckdns.org`

## 3) Endpoints útiles para prueba

- Salud: `GET /v2/health`
- Rutas V2 (ejemplo): `GET /v2/...` (ver documentación de la API)

## 4) Despliegue y logs

- Ver contenedores: `docker ps`
- Logs del servicio:
  
  ```powershell
  docker logs -f toxinas_app
  ```
- Reiniciar servicio:
  
  ```powershell
  docker compose restart app
  ```

## 5) Notas

- Si necesitas cambiar el puerto externo, edita `docker-compose.yml` y ajusta la regla de NPM.
- El servicio `dev` sigue exponiendo `5001:5001` para desarrollo local (puede usarse con `docker compose up dev`).
- En producción se recomienda mantener `DEBUG=0`.
