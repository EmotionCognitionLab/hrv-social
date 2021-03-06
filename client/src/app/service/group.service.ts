import { Injectable } from '@angular/core';
import { Http, Headers, URLSearchParams } from '@angular/http';
import { RequestMethod, RequestOptions, RequestOptionsArgs } from '@angular/http';
import { Response, ResponseContentType } from '@angular/http';

import { Observable } from 'rxjs/Observable';
import 'rxjs/add/operator/map';

import { DynamoDB } from '../../../node_modules/aws-sdk/';

import { AuthService } from './auth.service';
import { DynamoService } from './dynamo.service';
import { LoggerService } from './logger.service';
import { Group } from '../model/group';
import { GroupMessage } from '../model/group-message';
import { User } from '../model/user';
import { environment } from '../../environments/environment';
import { query } from '@angular/core/src/animation/dsl';

@Injectable()
export class GroupService {
    tableName = environment.groupsTable;
    msgTableName = environment.groupMsgsTable;
    basePath = environment.apiBasePath;

    constructor(private dyno: DynamoService, private authService: AuthService, private logger: LoggerService, protected http: Http) {}

    addGroup(newGroup: Group): Promise<string> {
        return this.dyno.docClient
        .then((docClient) => {
            return docClient.put({
            TableName: this.tableName,
            Item: {
                'name': newGroup.name,
                'startDate': newGroup.startDate,
                'endDate': newGroup.endDate,
                'earnings': newGroup.earnings
            }
        }).promise();
        })
        .then(() => 'Added group "' + newGroup.name + '".')
        .catch((err) => {
            this.logger.error(`Error saving group ${JSON.stringify(newGroup)}`, err);
            throw(err);
        });
    }

    getGroup(name: string): Promise<Group | undefined> {
        return this.dyno.docClient
        .then((docClient) => {
            return docClient.get({
                TableName: this.tableName,
                Key: { 'name': name }
            }).promise();
        })
        .then((item) => {
            if (item.Item === undefined) {
                return undefined;
            }
            const g = new Group(item.Item.name, item.Item.startDate, item.Item.endDate);
            if (item.Item.earnings !== undefined) {
                g.earnings = item.Item.earnings;
            }
            return g;
        })
        .catch((err) => {
            this.logger.error(`Error getting group ${name}`, err);
            return undefined;
        });
    }

    getAllGroups(): Promise<Group[]> {
        const result: Group[] = [];
        return this._getAllGroups(result);
    }

    // TODO test lastEvaldKey
    private _getAllGroups(result: Group[], lastEvaldKey?: DynamoDB.Key): Promise<Group[]> {
        return this.dyno.docClient
        .then((docClient) => {
            const params = {
                TableName: this.tableName
            };
            if (lastEvaldKey !== undefined) {
                params['ExclusiveStartKey'] = lastEvaldKey;
            }
            return docClient.scan(params).promise();
        })
        .then((scanResult) => {
            if (scanResult.Items === undefined) {
                throw new Error('No groups found.');
            }
            scanResult.Items.forEach(i => {
                const g = new Group(i.name, i.startDate, i.endDate);
                if (i.earnings !== undefined) {
                    g.earnings = i.earnings;
                }
                result.push(g);
            });
            if (scanResult.LastEvaluatedKey !== undefined) {
                return this._getAllGroups(result, scanResult.LastEvaluatedKey);
            }
            return result;
        })
        .catch((err) => {
            this.logger.error('Error getting all groups', err);
            return result;
        });
    }

    /**
     *
     * @summary Create a new message for the group the caller belongs to. (Of, for admins, any group.)
     * @param message The message to send to the group
     * @param groupName The name of the group you wish to post a message to. Only admins may post to groups they are not a member of - anyone else will receive a 401 Unauthorized response.
     */
    public createGroupMessage(message?: GroupMessage, groupName?: string, extraHttpRequestParams?: any): Observable<GroupMessage> {
        return this.createGroupMessageWithHttpInfo(message, groupName, extraHttpRequestParams)
            .map((response: Response) => {
                if (response.status === 204) {
                    return undefined;
                } else {
                    return response.json() || {};
                }
            });
    }

    /**
     * Create a new message for the group the caller belongs to. (Of, for admins, any group.)
     *
     * @param message The message to send to the group
     * @param groupName The name of the group you wish to post a message to. Only admins may post to groups they are not a member of - anyone else will receive a 401 Unauthorized response.
     */
    public createGroupMessageWithHttpInfo(message?: GroupMessage, groupName?: string, extraHttpRequestParams?: any): Observable<Response> {
        const path = this.basePath + '/group/messages';

        const queryParameters = new URLSearchParams();
        if (groupName !== undefined && groupName !== null) {
            queryParameters.set('group_name', <any>groupName);
        }

        // to determine the Content-Type header
        const consumes: string[] = [
            'application/json'
        ];

        // to determine the Accept header
        const produces: string[] = [
            'application/json'
        ];

        const headers = new Headers();
        headers.set('Content-Type', 'application/json');

        let requestOptions: RequestOptionsArgs = new RequestOptions({
            method: RequestMethod.Post,
            body: message == null ? '' : JSON.stringify(message), // https://github.com/angular/angular/issues/10612
            search: queryParameters,
            withCredentials: false
        });
        // https://github.com/swagger-api/swagger-codegen/issues/4037
        if (extraHttpRequestParams) {
            requestOptions = (<any>Object).assign(requestOptions, extraHttpRequestParams);
        }

         // authentication (basic-user) required
        const tokenPromise = this.authService.getAccessToken();
        return Observable.fromPromise(tokenPromise).flatMap((accessToken) => {
            headers.set('Authorization', accessToken);
            requestOptions.headers = headers;
            return this.http.request(path, requestOptions);
        });
    }

     /**
     *
     * @summary Delete a specific group message. Returns the updated message, or the original if an error occurs.
     * @param msg The message to be deleted
     */
    public deleteGroupMessage(msg: GroupMessage, extraHttpRequestParams?: any): Promise<GroupMessage> {
        return this.dyno.docClient
        .then((docClient) => {
            const params = {
                TableName: environment.groupMsgsTable,
                Key: { group: msg.group, date: msg.date },
                UpdateExpression: 'set original=if_not_exists(original, :body), body=:deleted',
                ExpressionAttributeValues: { ':body': msg.body, ':deleted': 'This message has been deleted.' },
                ReturnValues: 'ALL_NEW'
            };
            return docClient.update(params).promise();
        })
        .then((res) =>  {
            const delMsg = new GroupMessage(res.Attributes.body);
            delMsg.group = res.Attributes.group;
            delMsg.date = res.Attributes.date;
            return delMsg;
        })
        .catch(err => {
                this.logger.error(`Error deleting group message ${JSON.stringify(msg)}`, err);
                return msg;
        });
    }

     /**
     * 
     * @summary Get all of the members of the group the caller belongs to. (Or, for admins, any group.)
     * @param groupName Name of the group whose members you want. If the caller is neither an admin nor a member of the group the response will be 401 Unauthorized.
     */
    public getGroupMembers(groupName?: string, extraHttpRequestParams?: any): Observable<User[]> {
        return this.getGroupMembersWithHttpInfo(groupName, extraHttpRequestParams)
            .map((response: Response) => {
                if (response.status === 204) {
                    return undefined;
                } else {
                    const memberArr = response.json() || [];
                    const result = [];
                    memberArr.forEach(member => {
                        result.push(User.fromJsonObj(member));
                    });
                    return result;
                }
            });
    }

     /**
     * Get all of the members of the group the caller belongs to. (Or, for admins, any group.)
     * 
     * @param groupName Name of the group whose members you want. If the caller is neither an admin nor a member of the group the response will be 401 Unauthorized.
     */
    public getGroupMembersWithHttpInfo(groupName?: string, extraHttpRequestParams?: any): Observable<Response> {
        const path = this.basePath + '/group/members';

        const queryParameters = new URLSearchParams();
        // const headers = new Headers(this.defaultHeaders.toJSON()); // https://github.com/angular/angular/issues/6845
        if (groupName !== undefined) {
            queryParameters.set('group_name', <any>groupName);
        }

        // to determine the Content-Type header
        const consumes: string[] = [
            'application/json'
        ];

        // to determine the Accept header
        const produces: string[] = [
            'application/json'
        ];

        // authentication (basic-user) required
        const tokenPromise = this.authService.getAccessToken();
        return Observable.fromPromise(tokenPromise).flatMap((accessToken) => {
            const headers = new Headers();
            headers.set('Authorization', accessToken);

            let requestOptions: RequestOptionsArgs = new RequestOptions({
                method: RequestMethod.Get,
                headers: headers,
                search: queryParameters,
                withCredentials: false
            });
            // https://github.com/swagger-api/swagger-codegen/issues/4037
            if (extraHttpRequestParams) {
                requestOptions = (<any>Object).assign(requestOptions, extraHttpRequestParams);
            }

            return this.http.request(path, requestOptions);
        });
    }

     /**
     * 
     * @summary Get all of the messages for the group the caller belongs to. (Or, for admins, any group.)
     * @param groupName Name of the group whose messages you want. If the caller is neither an admin nor a member of the group the response will be 401 Unauthorized.
     */
    public getGroupMessages(since: number, groupName?: string, extraHttpRequestParams?: any): Observable<GroupMessage[]> {
        return this.getGroupMessagesWithHttpInfo(since, groupName, extraHttpRequestParams)
            .map((response: Response) => {
                if (response.status === 204) {
                    return undefined;
                } else {
                    return response.json() || {};
                }
            });
    }


    /**
     * Get all of the messages for the group the caller belongs to. (Or, for admins, any group.)
     * 
     * @param groupName Name of the group whose messages you want. If the caller is neither an admin nor a member of the group the response will be 401 Unauthorized.
     */
    public getGroupMessagesWithHttpInfo(since: number, groupName?: string, extraHttpRequestParams?: any): Observable<Response> {
        const path = this.basePath + '/group/messages';

        const queryParameters = new URLSearchParams();
        queryParameters.set('since', since.toString());
        if (groupName !== undefined) {
            queryParameters.set('group_name', <any>groupName);
        }

        // authentication (basic-user) required
        const tokenPromise = this.authService.getAccessToken();
        return Observable.fromPromise(tokenPromise).flatMap((accessToken) => {
            const headers = new Headers();
            headers.set('Authorization', accessToken);

            let requestOptions: RequestOptionsArgs = new RequestOptions({
                method: RequestMethod.Get,
                headers: headers,
                search: queryParameters,
                withCredentials: false
            });
            // https://github.com/swagger-api/swagger-codegen/issues/4037
            if (extraHttpRequestParams) {
                requestOptions = (<any>Object).assign(requestOptions, extraHttpRequestParams);
            }

            return this.http.request(path, requestOptions);
        });
    }

    /**
     * Updates various Google spreadsheets with users' HRV training data.
     * @param getAllGroups If set, updates data for all groups. If not, updates data only for active groups.
     * @param week Use a number between 0 and 5 to update a specific week. Leave unset to update the current week.
     * @param extraHttpRequestParams
     */
    public updateSpreadsheets(week?: number, getAllGroups?: boolean, extraHttpRequestParams?: any): Observable<Object> {
        return this.updateSpreadsheetsWithHttpInfo(week, getAllGroups, extraHttpRequestParams)
            .map((response: Response) => {
                return response.json();
            });
    }

    public updateSpreadsheetsWithHttpInfo(week?: number, getAllGroups?: boolean, extraHttpRequestParams?: any): Observable<Object> {
        const path = this.basePath + '/spreadsheets/update';

        const queryParameters = new URLSearchParams();
        if (getAllGroups !== undefined && getAllGroups) {
            queryParameters.set('getAllGroups', getAllGroups.toString());
        }
        if (week !== undefined && week !== null) {
            queryParameters.set('week', week.toString());
        }

        // authentication (basic-user) required
        const tokenPromise = this.authService.getAccessToken();
        return Observable.fromPromise(tokenPromise).flatMap((accessToken) => {
            const headers = new Headers();
            headers.set('Authorization', accessToken);

            let requestOptions: RequestOptionsArgs = new RequestOptions({
                method: RequestMethod.Get,
                headers: headers,
                search: queryParameters,
                withCredentials: false
            });
            // https://github.com/swagger-api/swagger-codegen/issues/4037
            if (extraHttpRequestParams) {
                requestOptions = (<any>Object).assign(requestOptions, extraHttpRequestParams);
            }

            return this.http.request(path, requestOptions);
        });
    }
}
