import { Component, inject, signal } from '@angular/core';
import { ReactiveFormsModule, FormBuilder, Validators, AbstractControl } from '@angular/forms';

@Component({
  selector: 'app-registerform',
  imports: [ReactiveFormsModule],
  templateUrl: './registerform.html',
  styleUrl: './registerform.scss',
})
export class Registerform {
  private fb = inject(FormBuilder);
  showPw = signal(false);
  showCf = signal(false);

  togglePw() {
    this.showPw.set(!this.showPw());
  }
  toggleCf() {
    this.showCf.set(!this.showCf());
  }

  form = this.fb.group(
    {
      name: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      company: [''],
      size: [''],
      role: [''],
      password: ['', [Validators.required, Validators.minLength(6)]],
      confirm: ['', Validators.required],
      tos: [false, Validators.requiredTrue],
    },
    { validators: [match('password', 'confirm')] },
  );

  submit() {
    if (this.form.invalid) return;
    console.log('SIGNUP', this.form.value);
    // TODO: conectar con AuthService
  }
}

function match(a: string, b: string) {
  return (group: AbstractControl) => {
    const A = group.get(a)?.value,
      B = group.get(b)?.value;
    return A && B && A === B ? null : { mismatch: true };
  };
}
