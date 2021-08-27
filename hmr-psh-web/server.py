import os
import sqlite3

from flask import Flask, request, render_template


class PoolLookup:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None

    def __enter__(self):
        return self

    def __exit__(self):
        return self

    def __ensure_connection(self):
        if not self.conn:
            self.conn = sqlite3.connect(database=self.db_path)

    def get_pool(self, pool_id):
        """ Gets a list of data about a pool or a sample in a pool
            Returns list of list: [[run ID, date, pool_id, well, comment, run number, list of samples], [... ], ...]
        """

        self.__ensure_connection()
        cur = self.conn.cursor()

        data_list = []
        if "POOL" not in pool_id:
            pool_id = '%' + pool_id + '%'
            sample = pool_id
            cur.execute('''SELECT pool_id FROM Samples where sample_id like %?%''',(sample,))
            pool_ids = cur.fetchall()
            for i in pool_ids:
                 data_list.append(self.get_pool(i))
            ## her kan man legge til PSH support
        else:
            cur.execute('''SELECT * FROM Pools where pool_id like ?''', (pool_id,))
            data = cur.fetchall()
            cur.execute('''SELECT * FROM Samples where pool_id like ?''', (pool_id,))
            all_samples = cur.fetchall()
            for i in data:
                samples = []
                for sample in all_samples:
                    if(sample[0] == i[0]):
                        samples.append(sample[1])
                data_list.append(list(i)+samples)
        return data_list







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
        "Pool ID",
        "Prøve: ",
        "Possisjon i kjøring: ",
        "Kommentar:"
    ]
    db = os.environ['DB_URL']
    pool_db = os.environ['POOLING_DB_URL']
    # db = "/var/tmp/psh.db"

    if request.method == 'POST':
        sample = request.form['sample']
        er_pool = isPool(sample)
        # lookup = SamplesLookup(db)
        pool_lookup = PoolLookup(pool_db)
        data = pool_lookup.get_pool(sample)
        # data = lookup.get_run(sample=sample)
        # if data:
        #     run_number = []
        #     for i in data:
        #         run_number.append(lookup.get_run_number(i[0]))
        #     # run_number = lookup.get_run_number(data[0][0])
        # else:
        #     run_number = -1

    return render_template('index.html', data=data, sample=sample, text=text, run_number=run_number)

def isPool(s):
    return "POOL" in s

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
