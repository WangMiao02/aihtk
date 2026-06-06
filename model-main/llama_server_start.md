# 运行模型

```
/opt/llama/bin/llama-cli -m /path/to/model.gguf -p "Hello"
```

# 启动 OpenAI 兼容 HTTP 服务


启动server推荐配置
```
/opt/llama/bin/llama-server \
    --model ./Qwen3.5-27B.Q4_K_M.gguf \
    --temp 0.6 \
    --top-p 0.95 \
    --top-k 20 \
    --min-p 0.00 \
    --host 0.0.0.0 \
    --port 38000 \
    --kv-unified \
    --cache-type-k q8_0 --cache-type-v q8_0 \
    --flash-attn on --fit on \
    --ctx-size 131072 
```