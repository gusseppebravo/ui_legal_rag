# Cache memory

You can disable cache in "app.py" by setting:


```python
st.session_state.backend = RAGClient(use_cache=False)
```