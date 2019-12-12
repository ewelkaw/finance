## App for making investment, buying and selling virtual shares :D

### Without docker
1. Requirements 
`pip install -r requirements.txt`

2. Preparing database 
`python db_request.py`

3. Running app
```python
export FLASK_APP=application
export FLASK_ENV=development
flask run
```

4. Running sqlite 
```bash
sqlite3 finance.db
select * from users;
select * from transactions;
```

### Using docker
1. make build
2. make run
3. got to: `http://0.0.0.0:5000/` and play
