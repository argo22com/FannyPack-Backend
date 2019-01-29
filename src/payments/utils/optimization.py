import pandas as pd
import numpy as np


class Optimization:
    """
        Class for reducing payment transactions between users
            - First step is to prepare data source
                - create empty transaction matrix by calling `Optimization.create_matrix(self, users)` method,
                  where parameter users is array of strings of users specifiers(e.g. 'id' or 'unique name')
                - load matrix from JSON with method `Optimization.load_from_json(json)
            - Payment can be added by calling method `Optimization.add_payment(drawee,pledger,amount)`
            - When matrix is ready, call `Optimization.run()` to get optimized matrix
    """

    matrix = []

# -------------------- DATA SOURCES ------------------------ #

    def create_matrix(self, users: [str]) -> matrix:

        users_no = len(users)

        init_matrix = np.zeros((users_no, users_no), dtype=float)
        # init_matrix = [[220, -110, -110], [-200, 400, -200], [-300, -300, 600]]
        self.matrix = pd.DataFrame(
            data=init_matrix,
            index=users,
            columns=users)

        return self.matrix

    def export_to_json(self) -> str:
        return self.matrix.to_json()

    def load_from_json(self, json: str):
        self.matrix = pd.read_json(json)

# -------------------- Optimization algorithms ------------------------ #
    def summarize_matrix(self) -> []:

        indexes = self.matrix.index
        no_users = len(indexes)

        # canvas matrix for sum values on diagonal
        summarized_matrix = np.zeros((no_users, no_users), dtype=float)

        for i in range(len(indexes)):
            summarized_matrix[i][i] = self.matrix[indexes[i]].sum()

        df = pd.DataFrame(
            data=summarized_matrix,
            index=indexes,
            columns=indexes)

        self.matrix = df

        print("SUMMARIZED MATRIX _____________________\n", self.matrix)

        return self.matrix.copy().values

    def optimize(self, summarized_matrix):
        max_index_x = -1
        max_index_y = -1
        min_index_x = -1
        min_index_y = -1
        max_v = -1
        min_v = 0

        for row in range(len(summarized_matrix[0])):
            for col in range(len(summarized_matrix[1])):
                if max_v < summarized_matrix[row][col]:
                    max_v = summarized_matrix[row][col]
                    max_index_x = row
                    max_index_y = col
                if min_v > summarized_matrix[row][col]:
                    min_v = summarized_matrix[row][col]
                    min_index_x = row
                    min_index_y = col

        # pokud soucet radku neni 0 - pak je nevyreseny dluh
        state = 0
        for row in summarized_matrix:
            for value in row:
                state += value
            if state != 0:
                break

        if state < -0.1 or state > 0.1:
            diff = max_v + min_v
            diff = round(diff, 2)
            min_v = round(min_v, 2)
            max_v = round(max_v, 2)
            if diff > 0:
                self.matrix.iloc[max_index_x, min_index_y] = min_v
                self.matrix.iloc[min_index_x, min_index_y] = 0
                summarized_matrix[min_index_x][min_index_y] = 0
                summarized_matrix[max_index_x][min_index_y] = 0
                summarized_matrix[max_index_x][max_index_y] = diff
            else:
                self.matrix.iloc[max_index_x, min_index_y] = -max_v
                self.matrix.iloc[min_index_x, min_index_y] = diff
                summarized_matrix[max_index_x][min_index_y] = 0
                summarized_matrix[max_index_x][max_index_y] = 0
                summarized_matrix[min_index_x, min_index_y] = diff
        else:
            return

        self.optimize(summarized_matrix)

    # ----------------------- Getters ---------------------------------#
    def get_biggest_pledger(self):
        indexes = self.matrix.index
        no_users = len(indexes)

        summarized_matrix = np.zeros((no_users, no_users), dtype=float)

        for i in range(len(indexes)):
            summarized_matrix[i][i] = self.matrix[indexes[i]].sum()

        df = pd.DataFrame(
            data=summarized_matrix,
            index=indexes,
            columns=indexes)

        min_index_x = -1
        min_v = 0

        for row in range(len(summarized_matrix[0])):
            for col in range(len(summarized_matrix[1])):
                if min_v > summarized_matrix[row][col]:
                    min_v = summarized_matrix[row][col]
                    min_index_x = row

        out = df.columns.values[min_index_x]
        return out

    # -------------------- Management Methods ------------------------ #
    def add_payment(self, drawee: str, pledger: str, amount: float):
        indexes = self.matrix.index
        if str(drawee) not in indexes:
            self.add_user(str(drawee))
            indexes = self.matrix.index
        if str(pledger) not in indexes:
            self.add_user(str(pledger))

        amount = round(amount, 2)

        self.matrix.loc[str(drawee), str(pledger)] += amount
        self.matrix.loc[str(drawee), str(drawee)] += -amount

    def add_user(self, name):
        index = [name]
        init_matrix = np.zeros(1, dtype=float)
        df = pd.DataFrame(
            data=init_matrix,
            index=index,
            columns=index)

        result = pd.concat([self.matrix, df], axis=1, sort=False)
        self.matrix = result.fillna(value=0)

    def run(self) -> matrix:
        summarized_m = self.summarize_matrix()
        self.optimize(summarized_m)
        return self.matrix
