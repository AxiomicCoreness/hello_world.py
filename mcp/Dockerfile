FROM python:3.12-slim
WORKDIR /app
COPY port380_mcp.py .
ENV PORT=380
EXPOSE 380
USER 1000
CMD ["python", "port380_mcp.py"]
