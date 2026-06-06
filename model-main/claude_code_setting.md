
# 修改 ~/.bashrc  

注释掉ANTHROPIC_AUTH_TOKEN 
使用ANTHROPIC_API_KEY

例子:
```
export ANTHROPIC_BASE_URL="http://127.0.0.1:38000"
export ANTHROPIC_API_KEY="sk-no-key-required"
#export ANTHROPIC_AUTH_TOKEN="$ABP_API_KEY" # 填写你的ABP虚拟账号 sk-xxx
export ANTHROPIC_DEFAULT_SONNET_MODEL="claude-sonnet-4.6" 
export ANTHROPIC_DEFAULT_OPUS_MODEL="claude-sonnet-4.6" 
export ANTHROPIC_DEFAULT_HAIKU_MODEL="claude-haiku-4.5"
export CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1
```
# 修改 ~/.claude/settings.json  

如果配置了~/.claude/settings.json 也要跟着改
要去掉ANTHROPIC_AUTH_TOKEN
改成ANTHROPIC_API_KEY
```
{
   "env": {
      "ANTHROPIC_BASE_URL": "http://127.0.0.1:38000",
      "ANTHROPIC_API_KEY": "sk-no-key-required",
      "ANTHROPIC_SMALL_FAST_MODEL": "gemini-3-flash",
      "ANTHROPIC_MODEL": "claude-sonnet-4.5",
      "CLAUDE_CODE_MAX_OUTPUT_TOKENS": "32000"
   }
}
```