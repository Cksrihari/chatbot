import pandas as pd


class ContingencyDetails:
    def __init__(self):
        file_path = 'Contingency Plan Details.csv'
        file_path_instr = 'Instructions_data.csv'
        self.df = pd.read_csv(file_path)
        self.df_instr = pd.read_csv(file_path_instr, encoding='ISO-8859-1')

    def get_peak_message(self, plan_code, train_status, service, peak_type):
        filtered_df = self.df[
            (self.df['plan_code'] == plan_code) &
            (self.df['train_status'] == train_status) &
            (self.df['service'] == service)
            ]
        if filtered_df.empty:
            return "No matching records found.", ""

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
        message = self.cont_plans(plan_code)
        delayed_time = f"{peak_value} per hour, {peak_message}" + "\n" + message
        return delayed_time

    def cont_plans(self, plan_code):
        filtered_df_instr = self.df_instr[
            (self.df['plan_code'] == plan_code)
        ]
        if filtered_df_instr.empty:
            return "No matching records found."

        instructions = filtered_df_instr.iloc[0]['instruction']
        resources = filtered_df_instr.iloc[0]['resources']
        infrastructure = filtered_df_instr.iloc[0]['crit_infra']
        staff_to_deploy = filtered_df_instr.iloc[0]['staff_deploy']
        alternate_transport = filtered_df_instr.iloc[0]['alt_trans']
        customer_message = filtered_df_instr.iloc[0]['cust_message']
        internal_message = filtered_df_instr.iloc[0]['internal_message']

        message = "Instruction to operators: \n" + instructions + "\n" + "Staff to Deploy:\n" + "\n" + staff_to_deploy + "\n" + "Alternative Transport:\n" + alternate_transport + "\n" + "Customer Message: \n" + customer_message + "\n" + "Internal Message: \n" + internal_message

        return message


if __name__ == "__main__":
    main = ContingencyDetails()
    peak_value, peak_message = main.get_peak_message('GE12', 'Amended', 'Greater Anglia', 'am_peak')
    print(f"{peak_value} per hour, {peak_message}")
