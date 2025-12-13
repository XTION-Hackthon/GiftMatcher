import uvicorn

if __name__ == "__main__":
    # 告诉 uvicorn 去 main 文件里找 app 变量
    # reload=True 表示你改代码它自动重启，适合开发
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
