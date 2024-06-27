import pandas as pd


class ContingencyDetails:
    def __init__(self):
        file_path = 'Contingency Plan Details.csv'
        self.df = pd.read_csv(file_path)

    def get_peak_message(self, plan_code, train_status, service, peak_type):
        # Filter the dataframe based on the given inputs
        filtered_df = self.df[
            (self.df['plan_code'] == plan_code) &
            (self.df['train_status'] == train_status) &
            (self.df['service'] == service)
        ]
        if filtered_df.empty:
            return "No matching records found.", ""

        # Determine which peak message to print
        if peak_type == 'am_peak':
            peak_value = filtered_df.iloc[0]['am_peak']
            peak_message = filtered_df.iloc[0]['am_peak_message']
        elif peak_type == 'pm_peak':
            peak_value = filtered_df.iloc[0]['pm_peak']
            peak_message = filtered_df.iloc[0]['pm_peak_message']
        elif peak_type == 'off_peak':
            peak_value = filtered_df.iloc[0]['off_peak']
            peak_message = filtered_df.iloc[0]['off_peak_message']
        else:
            return "Invalid peak type.", ""
        delayed_time = f"{peak_value} per hour, {peak_message}"
        return delayed_time


# Example usage

if __name__ == "__main__":
    main = ContingencyDetails()
    peak_value, peak_message = main.get_peak_message('GE12', 'Amended', 'Greater Anglia', 'am_peak')
    print(f"{peak_value} per hour, {peak_message}")
