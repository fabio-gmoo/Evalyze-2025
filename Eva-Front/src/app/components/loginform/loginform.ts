import { Component, inject, signal } from '@angular/core';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';

@Component({
  selector: 'app-loginform',
  imports: [ReactiveFormsModule],
  templateUrl: './loginform.html',
  styleUrl: './loginform.scss',
})
export class Loginform {
  private fb = inject(FormBuilder);
  show = signal(false);

  form = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(6)]],
    remember: [false],
  });

  submit() {
    if (this.form.invalid) return;
    console.log('LOGIN', this.form.value);
    // TODO: conectar con AuthService
  }

  toggleShow() {
    this.show.set(!this.show());
  }
}
