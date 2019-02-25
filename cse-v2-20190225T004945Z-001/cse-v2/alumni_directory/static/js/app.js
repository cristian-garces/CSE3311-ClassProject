const search_new_user = $(".search_new_user");


search_new_user.search({
    minCharacters: 2,
    selectFirstResult: true,
    searchDelay: 50,
    showNoResults: true,
    apiSettings : {
        onResponse: function(APIResponse) {
            let response = {
                results: []
            };

            $.each(APIResponse, function(index, item) {
                if(item.uta_id.trim()){
                    response.results.push({
                        title: ((item.first_name != null ? item.first_name: "") + (item.middle_name != null ? " " + item.middle_name + " ": " ") + (item.last_name != null ? item.last_name: "")).replace("   ", " "),
                        description: item.uta_id,
                        email: item.email,
                        net_id: item.net_id
                    });
                }
            });
            return response
        },
        // url: '../../../../../api/search/alumni/name/{query}'
        url: ' ../../mavapps/api/search/alumni/name/{query}'
        
    },
    onSelect: function(selection, APIResponse) {
        $("#selected_user_id").val(selection.description);
        $("#selected_user_net_id").val(selection.net_id);
        applicant_name = selection.title;
        applicant_email = selection.email;
        applicant_id  = selection.description;
        return true;
    },
});