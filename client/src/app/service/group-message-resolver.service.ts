import { Injectable } from '@angular/core';
import { Observable } from 'rxjs/Observable';
import 'rxjs/add/operator/map';
import 'rxjs/add/operator/take';
import { Router, Resolve, RouterStateSnapshot,
         ActivatedRouteSnapshot } from '@angular/router';

import { GroupMessage } from '../model/group-message';
import { GroupService } from './group.service';

@Injectable()
export class GroupMessageResolverService implements Resolve<GroupMessage[]> {

    constructor(private groupService: GroupService, private router: Router) { }

    resolve(route: ActivatedRouteSnapshot, state: RouterStateSnapshot): Observable<GroupMessage[]> {
        const groupName = route.paramMap.get('group_name');
        return this.groupService.getGroupMessages(groupName).take(1).map(messages => {
            if (messages) {
                return messages;
            } else {
                // TODO if the group just doesn't exist then /login is not the right place to send them
                this.router.navigate(['/login']);
                return null;
            }
        });
    }
}
