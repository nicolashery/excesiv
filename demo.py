import random

def _num_gen(method, rand_max):
    """Generate a random number for demo data"""
    if method == 'header':
        return round(random.choice(\
            [random.random()*rand_max, -random.random()*rand_max]), 1)
    else:
        return round(random.choice(\
            [0, random.random()*rand_max, -random.random()*rand_max]), 1)

def _to_float(value):
    """Convert value to float, invalid strings and None become 0"""
    try:
        res = float(value)
    except (ValueError, TypeError):
        res = 0
    return res

def generate_demo_data(n_rows, rand_max):
    """Generates demo data to write to Excel template"""
    # Full data object example
    data = {
        'header': {
            'header_w': 0,
            'header_wr': 0,
            'array_header_w': [0, 0, 0],
            'array_header_wr': [0, 0, 0]
        },
        'rows': [
            {
                'id_number': 1,
                'data_w': 0,
                'data_wr': 0,
                'array_data_w': [0, 0, 0],
                'array_data_wr': [0, 0, 0]
            }
        ]
    }
    # Header data
    data['header'] = {
        'header_w': _num_gen('header', rand_max),
        'header_wr': _num_gen('header', rand_max),
        'array_header_w': [_num_gen('header', rand_max) for i in range(3)],
        'array_header_wr': [_num_gen('header', rand_max) for i in range(3)]
    }
    # Row data
    rows = []
    for i in range(1, n_rows + 1):
        rows.append({
            'id_number': i,
            'data_w': _num_gen('row', rand_max),
            'data_wr': _num_gen('row', rand_max),
            'array_data_w': [_num_gen('row', rand_max) for i in range(3)],
            'array_data_wr': [_num_gen('row', rand_max) for i in range(3)]
            })
    data['rows'] = rows
    return data

def interpret_demo_data(data):
    """Interpret demo data read from Excel template"""
    # Some statistics we will return
    n_header_items = 0
    n_header_items_new = 0
    n_row_items = 0
    n_row_items_new = 0
    sum_header_items = 0
    sum_header_items_new = 0
    sum_row_items = 0
    sum_row_items_new = 0
    # Header data
    for k, v in data['header'].iteritems():
        # Convert all header values to list of floats
        if not isinstance(v, list):
            v = [v]
        v = [_to_float(x) for x in v]
        # Now use list methods to get statistics
        if k.endswith('_r'):
            n_header_items_new = n_header_items_new + len(v)
            sum_header_items_new = sum_header_items_new + sum(v)
        n_header_items = n_header_items + len(v)
        sum_header_items = sum_header_items + sum(v)
    # Row data
    for row in data['rows']:
        for k, v in row.iteritems():
            if not isinstance(v, list):
                v = [v]
            v = [_to_float(x) for x in v]
            if k.endswith('_r'):
                n_row_items_new = n_row_items_new + len(v)
                sum_row_items_new = sum_row_items_new + sum(v)
            n_row_items = n_row_items + len(v)
            sum_row_items = sum_row_items + sum(v)
    response = {
        'n_header_items': n_header_items,
        'n_header_items_new': n_header_items_new,
        'n_row_items': n_row_items,
        'n_row_items_new': n_row_items_new,
        'sum_header_items': sum_header_items,
        'sum_header_items_new': sum_header_items_new,
        'sum_row_items': sum_row_items,
        'sum_row_items_new': sum_row_items_new
    }
    return response

def test():
    import os
    import json
    from excesiv import Excesiv
    xs = Excesiv()
    xs.connect_db('mongodb://localhost/excesiv')
    template = 'test'
    print 'Testing write'
    n_rows = 10
    rand_max = 3
    data = generate_demo_data(n_rows, rand_max)
    task = {'assigned': False, 'type': 'write', 
            'template': '%s.xlsx' % template, 
            'data': data, 
            'attachment_filename': '%s.xlsx' % template}
    result = xs.process_task(task)
    file_url = '/api/files/%s' % result['file_id']
    print "File: http://localhost:5000%s" % file_url
    print 'Testing read'
    filename = 'task_%s.xlsx' % template
    content_type = \
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    f = open(filename, 'rb')
    file_id = xs.fs.put(f, filename=filename, content_type=content_type, 
                    label='task', attachment_filename='%s.xlsx' % template)
    # Create and process new task
    task = {'assigned': False, 'type': 'read', 'file_id': file_id}
    result = xs.process_task(task)
    response = interpret_demo_data(result['data'])
    print json.dumps(response, sort_keys=True, indent=2)

if __name__ == '__main__':
    # Some testing
    test()

