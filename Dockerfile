FROM python:3.10-slim
ADD signature.py /signature.py
RUN pip install requests
ENV TERM=xterm
#ENV PYTHONUNBUFFERED=1
CMD ["python3", "/signature.py"]