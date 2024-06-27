import pandas as pd

class ContingencyInstructions:
    def __init__(self):
        file_path = 'Instruction Plan Details.csv'
        self.df = pd.read_csv(file_path)

    def get_instruction_message(self, code_plan, operator):
        # Filter the dataframe based on the given inputs
        filtered_df = self.df[
            (self.df['code_plan'] == code_plan) &
            (self.df['operator'] == operator)
            ]

        if filtered_df.empty:
            return "No matching records found."

        # Get all messages
        messages = filtered_df['message'].tolist()

        # # Print all messages
        # for message in messages:
        #     print(message)

        return messages

if __name__ == "__main__":
    main = ContingencyInstructions()
    messages = main.get_instruction_message('GE09', 'INS-08')
    for message in messages:
        print(message)
