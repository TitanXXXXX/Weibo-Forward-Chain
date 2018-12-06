from handle_fwd import handle_one_web
import json

def split_childs_and_descendents(parent_node_list,current_node_list):
    parent_name_index = [item.usr_info['usr_name'] for item in parent_node_list]
    child_list = []
    descendant_list = []
    for item in current_node_list:
        if item.parent_name in parent_name_index:
            child_list.append(item)
        else:
            descendant_list.append(item)
    return (child_list,descendant_list)


def form_tree_of_chain(Parent_node_list,Decendant_node_list):
    print("Forming to tree....")
    (current_node_list,decsendant_node_list) = split_childs_and_descendents(Parent_node_list,Decendant_node_list)
    if decsendant_node_list == []:
        return [[item,] for item in current_node_list]
    child_node_list = form_tree_of_chain(current_node_list,decsendant_node_list)
    current_tree = []
    for parent in current_node_list:
        branch_list = [parent,]
        for child in child_node_list:
            if child[0].parent_name == parent.usr_info['usr_name']:
                branch_list.append(child)
        for cur_child  in branch_list[1:]:
            if cur_child:
                child_node_list.remove(cur_child)
        current_tree.append(branch_list)
    return current_tree


def handle_a_listtree_to_dictlist(src_list):
    #the children's parent is the caller
    child_list = []
    for item in src_list:
        if len(item) > 1:
            #item is a list which means the node has his children, and the first
            #element in item is child, the following are gransons list
            child_node = item.pop(0)
            grandson_list = handle_a_listtree_to_dictlist(item)
            child_list.append({
                'name': child_node.usr_info['usr_name'],
                'value': child_node.subfwd_quant,
                'children':grandson_list
            })
        else:
            #item is a fwd_node instance
            child_list.append({
                'name':item[0].usr_info['usr_name'],
                'value':item[0].subfwd_quant
            })
    return child_list

def transfer_tree_to_json(root_node,list_of_tree_nodes):
    children_list = handle_a_listtree_to_dictlist(list_of_tree_nodes)
    target_dict = {
        'name':root_node.usr_info['usr_name'],
        'value':root_node.subfwd_quant,
        'children':children_list
    }
    return target_dict

def run(source_web):
    (root_node,list_of_fwd_nodes) = handle_one_web(source_web)

    fwd_name_index = [item.usr_info['usr_name'] for item in list_of_fwd_nodes]
    fwd_name_index.append(root_node.usr_info['usr_name'])
    comment_fwds_list = []
    for item in list_of_fwd_nodes:
        if item.parent_name not in fwd_name_index:
            comment_fwds_list.append(item)
            list_of_fwd_nodes.remove(item)


    result = form_tree_of_chain([root_node,],list_of_fwd_nodes)
    dict_result = transfer_tree_to_json(root_node,result)

    comment_fwd_childern =  []
    for item in comment_fwds_list:
        comment_fwd_childern.append({
            'name':item.parent_name,
            'value':1,
            'children':[
                {
                    'name':item.usr_info['usr_name'],
                    'value':item.subfwd_quant
                }
            ]
        })

    dict_result['children'] = dict_result['children']+comment_fwd_childern

    return json.dumps(dict_result,ensure_ascii=False)

