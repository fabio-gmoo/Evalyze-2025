import { Component, inject, signal, computed, EventEmitter, Output } from '@angular/core';
import {
  ReactiveFormsModule,
  FormBuilder,
  Validators,
  NonNullableFormBuilder,
} from '@angular/forms';
import { Auth } from '@services/auth';
import { RouterLink } from '@angular/router';

type Role = 'company' | 'candidate';

@Component({
  selector: 'app-loginform',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  templateUrl: './loginform.html',
  styleUrl: './loginform.scss',
})
export class Loginform {
  @Output() loginSuccess = new EventEmitter<Role>();

  show = signal(false);
  loading = signal(false);
  errorMsg = signal<string | null>(null);

  private fb: NonNullableFormBuilder = inject(FormBuilder).nonNullable;
  private auth = inject(Auth);

  form = this.fb.group({
    email: this.fb.control('', { validators: [Validators.required, Validators.email] }),
    password: this.fb.control('', { validators: [Validators.required, Validators.minLength(6)] }),
    remember: this.fb.control(false),
    role: this.fb.control<Role>('company'),
  });

  disabled = computed(() => this.loading() || this.form.invalid);

  toggleShow() { this.show.set(!this.show()); }
  setRole(r: Role) { this.form.controls.role.setValue(r); }

  submit() {
    if (this.loading() || this.form.invalid) return;

    this.loading.set(true);
    this.errorMsg.set(null);

    const { email, password, role, remember } = this.form.getRawValue();

    this.auth.login({ email, password, role }).subscribe({
      next: (_user) => {
        try {
          const storage = remember ? localStorage : sessionStorage;
          storage.setItem('role', role!);
          sessionStorage.setItem('justLoggedIn', '1'); // <- bandera anti-bloqueo guard
        } catch {}

        this.loginSuccess.emit(role!);
      },
      error: (err) => {
        let msg = 'No se pudo iniciar sesión';
        if (err?.error?.role) msg = err.error.role;
        else if (err?.error?.detail) msg = err.error.detail;
        else if (err?.error?.non_field_errors) msg = err.error.non_field_errors[0];
        this.errorMsg.set(msg);
        this.loading.set(false);
      },
      complete: () => this.loading.set(false),
    });
  }
}
