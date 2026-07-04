proto:
    uv run -m grpc_tools.protoc -I=./proto --python_out=./src/pisa_api --pyi_out=./src/pisa_api --grpc_python_out=./src/pisa_api ./proto/*.proto
    sed -i 's/^import \(.\+\) as/from . import \1 as/' src/pisa_api/*.py
    sed -i 's/^import \(.*_pb2\) as/from . import \1 as/' src/pisa_api/*.pyi

clean:
    rm -rf src/pisa_api/*pb2*.py src/pisa_api/*pb2*.pyi
