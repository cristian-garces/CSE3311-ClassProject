EMAILS = {
    "submit_request": {
        "text": {
            True: "Dear {0},\nA previously returned reimbursement request has been resubmitted "
                  "on behalf of {1} {2}, please process or return this request at: "
                  "{3}reimbursement/view/requests/\n{8}"
                  "Summary:\nTitle: {4}\nRequester: {1} {2}\nPayee: {5} ({6})\nTotal: ${7}\n"
                  "Regards,\n\nCSE Webmaster\n"
                  "{3}reimbursement/",
            False: "Dear {0},\nA reimbursement request has been opened on behalf of {1} {2}, "
                   "please process or return this request at: {3}reimbursement/view/requests/\n{8}"
                   "Summary:\nTitle: {4}\nRequester: {1} {2}\nPayee: {5} ({6})\nTotal: ${7}\n"
                   "Regards,\n\nCSE Webmaster\n"
                   "{3}reimbursement/"
        },
        "html": {
            True: """
                    <html>
                        <body>
                            <p>
                            Dear {0},
                            </p>
                            <p>
                                A previously returned reimbursement request has been resubmitted on behalf of {1} {2}, please process or return this request by clicking <a href="{3}reimbursement/view/requests/">this link</a>.
                                {8}
                            </p>
                            <p>
                                Summary:<br>
                                Title: {4}<br>
                                Requester: {1} {2}<br>
                                Payee: {5} ({6})<br>
                                Total: ${7}
                            </p>
                            <p>
                                Regards,<br>
                                <br>
                                CSE Webmaster<br>
                                <a href="{3}reimbursement/">CSE Reimbursement App</a><br>
                            </p>
                        </body>
                    </html>
                """,
            False: """
                    <html>
                        <body>
                            <p>
                            Dear {0},
                            </p>
                            <p>
                                A reimbursement request has been opened on behalf of {1} {2}, please process or return this request by clicking <a href="{3}reimbursement/view/requests/">this link</a>.
                                {8}
                            </p>
                            <p>
                                Summary:<br>
                                Title: {4}<br>
                                Requester: {1} {2}<br>
                                Payee: {5} ({6})<br>
                                Total: ${7}
                            </p>
                            <p>
                                Regards,<br>
                                <br>
                                CSE Webmaster<br>
                                <a href="{3}reimbursement/">CSE Reimbursement App</a><br>
                            </p>
                        </body>
                    </html>
                """
        }
    },
    "process_request": {
        "text": {
            True: {
                True: "Dear {0} {1},\nThe request that you submitted on {2} for ${3} has been "
                      "processed by {4} ({5}), UT Share transaction number: {6}, and is currently "
                      "being evaluated. You may have already received a request for approval from UT "
                      "Share (https://www.uta.edu/utshare) with respect to this reimbursement or you "
                      "may soon receive it. Please make sure to act timely when you receive this "
                      "notification. You can also review your submission at {11}reimbursement/ "
                      ".{7}"
                      "\n\nSummary:\nTitle: {8}\nRequester: {0} {1}\nPayee: {9} ({10})\nTotal: ${3}\n"
                      "Regards,\n\nCSE Webmaster\n"
                      "{11}reimbursement/",
                False: "Dear {0},\nThe request to reimburse you submitted on {1} for ${2} by {3} {4}"
                       " has been processed by {5} ({6}), UT Share transaction number: {7}, and is "
                       "currently being evaluated. You may have already received a request for approval"
                       " from UT Share (https://www.uta.edu/utshare) with respect to this reimbursement"
                       " or you may soon receive it. Please make sure to act timely when you "
                       "receive this notification. You can also review your submission at {11}reimbursement/.{8}"
                       "\n\nSummary:\nTitle: {9}\nRequester: {3} {4} ({10})\nPayee: {0}\nTotal: ${2}\n"
                       "Regards,\n\nCSE Webmaster\n"
                       "{11}reimbursement/"
            },
            False: {
                True: "Dear {0} {1},\nThe request that you submitted on {2} for ${3} has been "
                      "reverted to an unprocessed status. You can find this submission at {10}reimbursement/."
                      "\nPlease see the message from {4} ({5}) below:"
                      "\n\n{6}"
                      "\n\nSummary:\nTitle: {7}\nRequester: {0} {1}\nPayee: {8} ({9})\nTotal: ${3}\n"
                      "Regards,\n\nCSE Webmaster\n"
                      "{10}reimbursement/",
                False: "Dear {0},\nThe request to reimburse you submitted on {1} for ${2} by {3} {4}"
                       " has been reverted to an unprocessed status.You can find this submission at {10}reimbursement/."
                       "\nPlease see the message from {5} "
                       "({6}) below:\n\n{7}"
                       "\n\nSummary:\nTitle: {8}\nRequester: {3} {4} ({9})\nPayee: {0}\nTotal: ${2}\n"
                       "Regards,\n\nCSE Webmaster\n"
                       "{10}reimbursement/"
            }
        },
        "html": {
            True: {
                True: """
                    <html>
                        <body>
                            <p>
                            Dear {0} {1},
                            </p>
                            <p>
                                The request that you submitted on {2} for ${3} has been processed by {4} ({5}), UT Share transaction number: {6}, and is currently being evaluated.
                                You may have already received a request for approval from <a href="https://www.uta.edu/utshare">UT Share</a> with respect to this reimbursement or you may soon receive it.
                                Please make sure to act timely when you receive this notification. You can also review your submission in the <a href="{11}reimbursement/">CSE Reimbursement App</a> at any time.{7}
                            </p>
                            <p>
                                Summary:<br>
                                Title: {8}<br>
                                Requester: {0} {1}<br>
                                Payee: {9} ({10})<br>
                                Total: ${3}
                            </p>
                            <p>
                                Regards,<br>
                                <br>
                                CSE Webmaster<br>
                                <a href="{11}reimbursement/">CSE Reimbursement App</a><br>
                            </p>
                        </body>
                    </html>
                """,
                False: """
                    <html>
                        <body>
                            <p>
                            Dear {0},
                            </p>
                            <p>
                                The request to reimburse you submitted on {1} for ${2} by {3} {4} has been processed by {5} ({6}), UT Share transaction number: {7}, and is currently being evaluated.
                                You may have already received a request for approval from <a href="https://www.uta.edu/utshare">UT Share</a> with respect to this reimbursement or you may soon receive it.
                                Please make sure to act timely when you receive this notification. You can also review your submission in the <a href="{11}reimbursement/">CSE Reimbursement App</a> at any time.{8}
                            </p>
                            <p>
                                Summary:<br>
                                Title: {9}<br>
                                Requester: {3} {4} ({10})<br>
                                Payee: {0}<br>
                                Total: ${2}
                            </p>
                            <p>
                                Regards,<br>
                                <br>
                                CSE Webmaster<br>
                                <a href="{11}reimbursement/">CSE Reimbursement App</a><br>
                            </p>
                        </body>
                    </html>
                """
            },
            False: {
                True: """
                    <html>
                        <body>
                            <p>
                            Dear {0} {1},
                            </p>
                            <p>
                                The request that you submitted on {2} for ${3} has been reverted to an unprocessed status. You can find this submission in the <a href="{10}reimbursement/">CSE Reimbursement App</a>.<br>
                                Please see the message from {4} ({5}) below: <br>
                                <blockquote style="border-left: 3px solid rgb(200, 200, 200); border-top-color: rgb(200, 200, 200); border-right-color: rgb(200, 200, 200); border-bottom-color: rgb(200, 200, 200); padding-left: 1ex; margin-left: 0.8ex; color: rgb(102, 102, 102);">
                                    <div style="color: rgb(0, 0, 0);">{6}</div>
                                </blockquote>
                            </p>
                            <p>
                                Summary:<br>
                                Title: {7}<br>
                                Requester: {0} {1}<br>
                                Payee: {8} ({9})<br>
                                Total: ${3}
                            </p>
                            <p>
                                Regards,<br>
                                <br>
                                CSE Webmaster<br>
                                <a href="{10}reimbursement/">CSE Reimbursement App</a><br>
                            </p>
                        </body>
                    </html>
                """,
                False: """
                    <html>
                        <body>
                            <p>
                            Dear {0},
                            </p>
                            <p>
                                The request to reimburse you submitted on {1} for ${2} by {3} {4} has been reverted to an unprocessed status. You can find this submission in the <a href="{10}reimbursement/">CSE Reimbursement App</a>.<br>
                                Please see the message from {5} ({6}) below:<br>
                                <blockquote style="border-left: 3px solid rgb(200, 200, 200); border-top-color: rgb(200, 200, 200); border-right-color: rgb(200, 200, 200); border-bottom-color: rgb(200, 200, 200); padding-left: 1ex; margin-left: 0.8ex; color: rgb(102, 102, 102);">
                                    <div style="color: rgb(0, 0, 0);">{7}</div>
                                </blockquote>
                            </p>
                            <p>
                                Summary:<br>
                                Title: {8}<br>
                                Requester: {3} {4} ({9})<br>
                                Payee: {0}<br>
                                Total: ${2}
                            </p>
                            <p>
                                Regards,<br>
                                <br>
                                CSE Webmaster<br>
                                <a href="{10}reimbursement/">CSE Reimbursement App</a><br>
                            </p>
                        </body>
                    </html>
                """
            }
        }
    },
    "return_request": {
        "text": "Dear {0} {1},\nThe request that you submitted on {2} for ${3} has been returned "
                "to you for editing. Please go to your view requests page "
                "({4}reimbursement/view/requests/) and click the edit link on the request or follow "
                "this link to edit it now: {4}reimbursement/edit/request/"
                "?user_id={5}&request_id={6}{7}"
                "\n\nSummary:\nTitle: {8}\nRequester: {0} {1}\nPayee: {9} ({10})\nTotal: ${3}\n"
                "Regards,\n\nCSE Webmaster\n"
                "{4}reimbursement/",
        "html": """
                    <html>
                        <body>
                            <p>
                            Dear {0} {1},
                            </p>
                            <p>
                                The request that you submitted on {2} for ${3} has been returned to you for editing.
                                Please go to your <a href="{4}reimbursement/view/requests/">view requests page</a> and click the edit link on the request
                                or click <a href="{4}reimbursement/edit/request/?user_id={5}&request_id={6}">this link</a> to edit it now.
                                {7}
                            </p>
                            <p>
                                Summary:<br>
                                Title: {8}<br>
                                Requester: {0} {1}<br>
                                Payee: {9} ({10})<br>
                                Total: ${3}
                            </p>
                            <p>
                                Regards,<br>
                                <br>
                                CSE Webmaster<br>
                                <a href="{4}reimbursement/">CSE Reimbursement App</a><br>
                            </p>
                        </body>
                    </html>
                """
    },
    "void_request": {
        "text": "Greetings,\nThe request that was submitted on {0} by {1} {2} "
                "has been voided. No further action is necessary at this time."
                "You can find this and other submissions at {8}reimbursement/."
                "{3}"
                "\n\nSummary:\nTitle: {4}\nRequester: {1} {2}\nPayee: {5} ({6})\nTotal: ${7}\n"
                "Regards,\n\nCSE Webmaster\n"
                "{8}reimbursement/",
        "html": """
                    <html>
                        <body>
                            <p>
                            Greetings,
                            </p>
                            <p>
                                The request that was submitted on {0} by {1} {2} has been voided. No further action is necessary at this time.
                                You can find this and other submissions in the <a href="{8}reimbursement/">CSE Reimbursement App</a>.
                                {3}
                            </p>
                            <p>
                                Summary:<br>
                                Title: {4}<br>
                                Requester: {1} {2}<br>
                                Payee: {5} ({6})<br>
                                Total: ${7}
                            </p>
                            <p>
                                Regards,<br>
                                <br>
                                CSE Webmaster<br>
                                <a href="{8}reimbursement/">CSE Reimbursement App</a><br>
                            </p>
                        </body>
                    </html>
                """
    }
}
