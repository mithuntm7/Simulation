import pandas as pd
from geopy.distance import great_circle
import datetime
import numpy as np

for j in range(12): 
    banner_on = 1.2
    banner_off = 1.0
    consolidated_report = pd.DataFrame()    
    for i in range(9):
        assi = 60
        t = assi
        order_data = pd.read_csv("D:\\Back ups\\python Simulation\\new\\himayatnagar\\data\\himayatnagar_order_data.csv")
        de_details = pd.read_csv("D:\\Back ups\\python Simulation\\new\\himayatnagar\\data\\himayatnagar_de_data.csv")
        de_details = de_details.iloc[:(90+j*5)]
        denumber = str(len(de_details)) + "_des" 
        #de_details.set_index("de_id", drop = False, inplace = True)
        de_details["dp_lat"] = de_details["de_lat"]
        de_details["dp_lng"] = de_details["de_lng"]
        de_details["delivery_time"] = 0

        start_time = 19.0
        order_data["prep_time"] = order_data["prep_time"]*60
        order_data["last_mile"] = order_data["last_mile"]*60
        order_data["actual_sla"] = order_data["actual_sla"]*60
        order_data["predicted_sla"] = order_data["predicted_sla"]*60
        order_data["actual_delay"] = order_data["actual_delay"]*60
        order_data["ordered_time_seconds"] = (order_data["ordered_time"] - start_time/24)*24.0*60*60

        final_order_data = pd.DataFrame(columns = ["order_id", "ordered_time","ordered_time_seconds", "de_id", "status", "de_assignment_delay_time", "de_wait_time",
                                                   "delivery_time", "simulated_sla","actual_sla", "predicted_sla","actual_delay","first_mile"])
        banner_orders = pd.DataFrame(columns = ["order_id", "order_time"]) 
        banner_time = pd.DataFrame(columns = ["time","interval"])
        banner_logs = pd.DataFrame(columns = ["time","banner_factor"])

        def remove_order_data(order):
            global order_data
            order_data= order_data[order_data.order_id != order.order_id]        #del order_data from orders #delete first row from orders


        def update_final_order_data(time):
            global final_order_data
            if len(final_order_data)>=1:
                final_order_data.loc[(final_order_data["delivery_time"]<time) & (final_order_data["status"]=="R"), "status"]="D"
            
        def update_locations(time):
            global de_details
            if(len(de_details[de_details["status"]=="R"])>0):
                de_details.loc[(de_details["delivery_time"]<time)&(de_details["status"]=="R"),"status"]="D"
                de_details.loc[de_details["status"] == "D", "de_lat"] = de_details[de_details["status"]=="D"].dp_lat
                de_details.loc[de_details["status"] == "D", "de_lng"] = de_details[de_details["status"]=="D"].dp_lng
         
        def get_time(start, end):
            speed = 15.0
            factor = 1.5
            distance = great_circle((start),(end)).kilometers
            time = 60*60*distance*factor/speed
            return time

        de_count = float(len(de_details))

        def check_banner(order_intake):    
            active_order_count = len(final_order_data[final_order_data["status"]=="R"]) + len(order_intake)
            banner_factor = active_order_count / de_count
            return float(banner_factor)
            
        def assign(order, boy_id):
            print "reached here"
            global de_details
            global final_order_data
            #d = datetime.datetime(2016, 9, 29, 8, 0)
            first_mile = get_time((float(order.rest_lat),float(order.rest_lng)),(float(de_details[de_details["de_id"]==boy_id].de_lat),
                                float(de_details[de_details["de_id"]==boy_id].de_lng)))
            ordered_to_picked_up = max(order.delay + first_mile, order.prep_time)


            if order.flag == 0:
                de_wait_time = order.prep_time - (order.delay + first_mile) 
                delivery_time = float(order.ordered_time_seconds) + ordered_to_picked_up +float(order.last_mile)
                simulated_sla =  ordered_to_picked_up + float(order.last_mile)

            else:
                de_wait_time = order.prep_time
                simulated_sla = order.delay + order.prep_time + first_mile + order.last_mile
                delivery_time = order.ordered_time_seconds + simulated_sla
                
            de_details.loc[de_details["de_id"] == boy_id, "order_id"] = order.order_id
            de_details.loc[de_details["de_id"] == boy_id, "status"] = "R"
            de_details.loc[de_details["de_id"] == boy_id, "dp_lat"] = order.cust_lat
            de_details.loc[de_details["de_id"] == boy_id, "dp_lng"] = order.cust_lng
            #de_details.loc[de_details["de_id"] == boy_id, "de_lat"] = order.cust_lat
            #de_details.loc[de_details["de_id"] == boy_id, "de_lng"] = order.cust_lng

            de_details.loc[de_details["de_id"] == boy_id, "delivery_time"] = delivery_time
            final_order_data = final_order_data.append({"order_id":order.order_id, "ordered_time":order.ordered_time,"ordered_time_seconds":order.ordered_time_seconds,
                            "de_id":boy_id,"status": "R", "de_assignment_delay_time" : order.delay, "de_wait_time":de_wait_time, "delivery_time": delivery_time,
                            "simulated_sla": simulated_sla,"actual_sla":order.actual_sla, "predicted_sla":order.predicted_sla, "actual_delay":order.actual_delay,
                                                        "first_mile" : first_mile},ignore_index = True)
            remove_order_data(order)
            print "and here"

        def find_match_assign(assignment):
            global de_details
            de = de_details[(de_details.status =="F") | (de_details.status=="D")]
            a = len(assignment)
            b = len(de)

            if a>0 and b > 0:    
                assignment["delay"] = t - assignment["ordered_time_seconds"]
                #assignment.loc[assignment["flag"]==1,"with_de_score"] = 0
                #assignment.loc[assignment["flag"]==0,"with_de_score"] = 0
                
                if(a>1):
                    h = max(assignment["delay"])
                    l = min(assignment["delay"])
                    assignment["delay_score"] = 1900*(assignment["delay"]-l)/(h-l)
                else:
                    assignment["delay_score"] = 1900
                de["waiting"] = t - de["delivery_time"]
                w = [[de.iloc[i].waiting for i in range(b)] for x in range(a)]
                w = np.array(w)
                top = w.max()
                floor = w.min()
                if top == floor:
                    floor = 0
                w = 500*(w-floor)/(top - floor)
                y = [[get_time((assignment.iloc[i].rest_lat,assignment.iloc[i].rest_lng),(de.iloc[j].de_lat,de.iloc[j].de_lng)) for j in range(b)] for i in range(a)]
                y = np.array(y)
                np.putmask(y,y>=40*60,40*60)
                counter = 0
                if (y==40*60).sum() == a*b:
                    exit
                else:
                    if (y>=40*60).sum() >= 1:
                        counter = 1
                    else :
                        counter = 0
                maxi = y.max()
                mini = y.min()
                y = 1880 + (y-mini)*(-1880)/(maxi-mini) 
                if counter == 1 :
                    np.putmask(y,y<=1,-10000)
                #z = [[assignment.iloc[i].with_de_score for x in range(b)] for i in range(a)]
                #z = np.array(z)

                x = [[assignment.iloc[i].delay_score for x in range(b)] for i in range(a)]
                x = np.array(x)
                total = y + x + w
                np.putmask(total,total<0,0)
                #+ z
                while all(all( v == 0 for v in total[i]) == True for i in range(a)) == False:
                    i,j = np.unravel_index(total.argmax(), total.shape)

                    if total[i][j] < 0:
                        total[:,j] = 0
                        total[i] = 0
                        exit

                    else:
                        print "assignining ",assignment.iloc[i].order_id
                        print"to",de.iloc[j].de_id 
                        assign(assignment.iloc[i], de.iloc[j].de_id)        
                        total[:,j] = 0
                        total[i] = 0

            del assignment
            
        activate = 1
        while order_data.empty!=1:
            #order_data = order_data.sort("ordered_time_seconds")
            update_final_order_data(t)
            update_locations(t)
            
            if activate == 1:
                assignment = order_data[order_data["ordered_time_seconds"]<=t]
                b = check_banner(assignment)
                if b > banner_on:
                    start = t
                    activate = 0
                    print "banner activated at ",t
                if t%assi == 0 and len(assignment) > 0:
                    find_match_assign(assignment)

            else:
                banners = order_data[(order_data["ordered_time_seconds"]<t) & (order_data["ordered_time_seconds"]> (t-20) )]
                for i in range(len(banners)):
                    banner_orders = banner_orders.append({"order_id" : banners.iloc[i].order_id,
                        "order_time":banners.iloc[i].ordered_time},ignore_index = True )      

                order_data = order_data[(order_data["ordered_time_seconds"]>=t) | (order_data["ordered_time_seconds"]<= t-20)]
                order_intake = order_data[order_data["ordered_time_seconds"] <= t]
                b = check_banner(order_intake)

                if b < banner_off:
                    print "banner deactivated at ",t
                    activate = 1
                    banner_time = banner_time.append({"time" : t - start, "interval":(start,t)}, ignore_index = True)                 

                if t%assi == 0:
                    assignment = order_data[order_data["ordered_time_seconds"]<=t]        
                    find_match_assign(assignment)

            banner_logs = banner_logs.append({"time" : t, "banner_factor":b}, ignore_index = True)
                
            t = t + 20

        k = str(int(de_count)) 
        l = str(int(10*banner_off))
        m = str(int(10*banner_on))
        nam = k+l+m
        o_name = denumber + nam
        final_order_data.to_csv("D:\\Back ups\\python Simulation\\new\\himayatnagar\\results\\%s_output.csv"%nam)
        banner_time.to_csv("D:\\Back ups\\python Simulation\\new\\himayatnagar\\results\\%s_banner_time.csv"%nam)
        banner_logs.to_csv("D:\\Back ups\\python Simulation\\new\\himayatnagar\\results\\%s_banner_logs.csv"%nam)
        banner_orders.to_csv("D:\\Back ups\\python Simulation\\new\\himayatnagar\\results\\%s_banner_orders.csv"%nam)

        av_assignment_delay = final_order_data["de_assignment_delay_time"].mean()/60
        banner_time_total =  banner_time["time"].sum()/3600
        banner_count = len(banner_time)
        no_of_banner_orders = len(banner_orders)
        no_of_orders_assigned = len(final_order_data)
        average_sla = final_order_data["simulated_sla"].mean()/60
        sla_75 = final_order_data["simulated_sla"].quantile(q = 0.75)/60
        assignment_delay_75 = final_order_data["de_assignment_delay_time"].quantile(q = 0.75)/60
        sla_compliance = float(len(final_order_data[final_order_data["simulated_sla"]<=final_order_data["predicted_sla"]]))/no_of_orders_assigned
        final_output = pd.DataFrame()

        final_output = final_output.append({"no_of_orders_assigned":no_of_orders_assigned,"banner_time_total":banner_time_total,
                        "no_of_banner_orders":no_of_banner_orders ,"banner_count":banner_count, 
                        "av_assignment_delay" : av_assignment_delay,"assignment_delay_75":assignment_delay_75,
                                           "average_sla":average_sla, "sla_75":sla_75, "sla_compliance":sla_compliance},ignore_index = True )
        
        final_output.to_csv("D:\\Back ups\\python Simulation\\new\\himayatnagar\\results\\%s_consolidated.csv"%nam)
        consolidated_report = consolidated_report.append({"banner_on":banner_on, "banner_off":banner_off,
                                                          "no_of_orders_assigned":no_of_orders_assigned,"banner_time_total":banner_time_total,
                        "no_of_banner_orders":no_of_banner_orders ,"banner_count":banner_count, 
                        "av_assignment_delay" : av_assignment_delay,"assignment_delay_75":assignment_delay_75,
                                           "average_sla":average_sla, "sla_75":sla_75, "sla_compliance":sla_compliance},ignore_index = True )

        del final_output
        del final_order_data
        del banner_time
        del banner_logs
        del order_data
        del de_details
        del assignment
        del banner_orders
        banner_on = banner_on + 0.1
        banner_off = banner_off + 0.1
    #print final_output
    consolidated_report.to_csv("D:\\Back ups\\python Simulation\\new\\himayatnagar\\results\\%s_consolidated_report.csv"%denumber)
    del consolidated_report
