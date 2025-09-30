import { Component, output } from '@angular/core';
import { Loginform } from '@widgets/loginform/loginform';

@Component({
  selector: 'app-login',
  imports: [Loginform],
  templateUrl: './login.html',
  styleUrl: './login.scss',
})
export class Login {
  signupClick = output<void>();
  loginSuccess = output<void>(); // ✅ Agregar output para propagar el éxito

  onLoginSuccess() {
    this.loginSuccess.emit();
  }
}
