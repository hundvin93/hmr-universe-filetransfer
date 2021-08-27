import os
import sqlite3

from flask import Flask, request, render_template


class SamplesLookup:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.conn:
            self.conn.close()

    def __ensure_connection(self):
        if not self.conn:
            self.conn = sqlite3.connect(database=self.db_path)

    def get_run(self, sample):
        self.__ensure_connection()
        cur = self.conn.cursor()
        cur.execute('''SELECT * FROM Run where sample_id=?''',(sample,))
        return cur.fetchall()

    def get_run_number(self, run_id):
        self.__ensure_connection()
        cur = self.conn.cursor()
        cur.execute('''SELECT run_number FROM RunsDay where run_id=?''', (str(run_id),))
        return cur.fetchone()[0]


app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    data = None
    sample = None
    run_number = None
    text = [
        "Kjøring: ",
        "Klokken: ",
        "Prøve: ",
        "Possisjon i kjøring: "
    ]
    # db = os.environ['POOLING_DB_URL']
    db = "/var/tmp/psh.db"
    if request.method == 'POST':
        sample = request.form['sample']
        lookup = SamplesLookup(db)
        data = lookup.get_run(sample=sample)
        if data:
            run_number =[]
            for i in data:
                run_number.append(lookup.get_run_number(i[0]))
            # run_number = lookup.get_run_number(data[0][0])
        else:
            run_number = -1

    return render_template('index.html', data=data, sample=sample, text=text, run_number=run_number)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
