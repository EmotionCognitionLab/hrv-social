import { BrowserModule } from '@angular/platform-browser';
import { FormsModule } from '@angular/forms';
import { NgModule } from '@angular/core';

import { AppComponent } from './app.component';
import { GroupsComponent } from './groups.component';
import { AppRoutingModule } from './app-routing.module';
import { RegisterComponent } from './register.component';
import { AuthService } from './auth.service';

@NgModule({
  declarations: [
    AppComponent,
    GroupsComponent,
    RegisterComponent
  ],
  imports: [
    BrowserModule,
    FormsModule,
    AppRoutingModule
  ],
  providers: [AuthService],
  bootstrap: [AppComponent]
})
export class AppModule { }
