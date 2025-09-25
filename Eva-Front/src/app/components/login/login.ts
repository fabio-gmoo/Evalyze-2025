import { Component, EventEmitter, Output } from '@angular/core';
import { Loginform } from '@/components/loginform/loginform';

@Component({
  selector: 'app-login',
  imports: [Loginform],
  templateUrl: './login.html',
  styleUrl: './login.scss',
})
export class Login {
  @Output() signupClick = new EventEmitter<void>();
}
