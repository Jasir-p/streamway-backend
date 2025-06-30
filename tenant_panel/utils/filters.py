import json

def parse_filter_params(filter_item):
    
    filter_type = 'month'
    start_date = None
    end_date = None

    if filter_item:
        try:
            filter_data = json.loads(filter_item)
            filter_type = filter_data.get('filter_type', 'month')
            start_date = filter_data.get('start_date')
            end_date = filter_data.get('end_date')
        except json.JSONDecodeError:
            pass

    return {
        "filter_type": filter_type,
        "start_date": start_date,
        "end_date": end_date
    }