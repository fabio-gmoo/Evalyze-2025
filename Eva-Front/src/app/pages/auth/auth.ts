import { Component, signal, Input } from '@angular/core';
import { Login } from '@/components/login/login';
import { Register } from '@/components/register/register';

type Mode = 'login' | 'signup';

@Component({
  selector: 'app-auth',
  imports: [Login, Register],
  templateUrl: './auth.html',
  styleUrl: './auth.scss',
})
export class Auth {
  mode = signal<Mode>('login');

  @Input() set startMode(value: Mode | undefined) {
    if (value) this.mode.set(value);
  }

  switchTo(next: Mode) {
    this.mode.set(next);
  }
}
