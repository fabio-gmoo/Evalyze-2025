import { Component, output } from '@angular/core';
import { Loginform } from '@widgets/loginform/loginform';

type Role = 'company' | 'candidate';

@Component({
  selector: 'app-login',
  imports: [Loginform],
  templateUrl: './login.html',
  styleUrl: './login.scss',
})
export class Login {
  signupClick = output<void>();
  // puede emitir con o sin rol; soporta ambos
  loginSuccess = output<void | Role>();

  // ya no esperamos $event; si algún día el widget emite rol, puedes
  // volver a aceptar un parámetro opcional: onLoginSuccess(role?: Role)
  onLoginSuccess() {
    this.loginSuccess.emit();
  }
}
